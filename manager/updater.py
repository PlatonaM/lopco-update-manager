"""
   Copyright 2020 InfAI (CC SES)

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""


__all__ = ("Updater", "UpdaterError", "CheckUpdatesError", "UpdateCheckInProgress")


from . import model
from .logger import getLogger
from .configuration import conf
from .util import getDelay
import urllib.parse
import threading
import datetime
import requests
import time
import json


logger = getLogger(__name__.split(".", 1)[-1])


class UpdaterError(Exception):
    pass


class CheckUpdatesError(UpdaterError):
    pass


class UpdateCheckInProgress(UpdaterError):
    pass


class NotFound(UpdaterError):
    pass


class UpdateError(UpdaterError):
    pass


class Updater(threading.Thread):
    def __init__(self):
        super().__init__(name="updater", daemon=True)
        self.__available_updates = dict()
        self.__lock = threading.Lock()

    def __checkImage(self, image: str) -> bool:
        resp = requests.get(
            url="{}/{}/{}".format(
                conf.DeploymentManager.url,
                conf.DeploymentManager.img_api,
                urllib.parse.quote(urllib.parse.quote(image, safe=''))
            )
        )
        if resp.ok:
            image_digests = resp.json()["digests"]
            image_digests = ",".join(image_digests)
            resp = requests.get(
                url="{}/{}/{}".format(
                    conf.DeploymentManager.url,
                    conf.DeploymentManager.dig_api,
                    urllib.parse.quote(urllib.parse.quote(image, safe=''))
                )
            )
            if resp.ok:
                remote_image_digest = resp.json()["digest"]
                if remote_image_digest not in image_digests:
                    return True
                else:
                    return False
            else:
                raise RuntimeError("{} - {}".format(resp.url, resp.status_code))
        else:
            raise RuntimeError("{} - {}".format(resp.url, resp.status_code))

    def __checkCoreImages(self):
        images = conf.Core.images.split(";")
        for image in images:
            try:
                if self.__checkImage(image):
                    self.__available_updates[image] = {
                        model.Update.type: model.UpdateType.core,
                        model.Update.entities: list(),
                        model.Update.time: '{}Z'.format(datetime.datetime.utcnow().isoformat())
                    }
            except Exception as ex:
                logger.warning("update check for '{}' failed - {}".format(image, ex))

    def __checkUserImages(self, url: str, type: str):
        resp = requests.get(url=url)
        if resp.ok:
            for key, value in resp.json().items():
                value = json.loads(value)
                image = value["image"]
                try:
                    if image not in self.__available_updates:
                        if self.__checkImage(image):
                            self.__available_updates[image] = {
                                model.Update.type: type,
                                model.Update.entities: [key],
                                model.Update.time: '{}Z'.format(datetime.datetime.utcnow().isoformat())
                            }
                    else:
                        if key not in self.__available_updates[image][model.Update.entities]:
                            self.__available_updates[image][model.Update.entities].append(key)
                except Exception as ex:
                    logger.warning("update check for '{}' failed - {}".format(image, ex))

    def __checkUpdates(self):
        logger.info("checking for updates ...")
        try:
            self.__lock.acquire()
            self.__available_updates.clear()
            self.__checkCoreImages()
            self.__checkUserImages(
                "{}/{}".format(conf.ProtocolAdapterRegistry.url, conf.ProtocolAdapterRegistry.api),
                model.UpdateType.protocol_adapter
            )
            self.__checkUserImages(
                "{}/{}".format(conf.WorkerRegistry.url, conf.WorkerRegistry.api),
                model.UpdateType.worker
            )
            self.__lock.release()
        except Exception as ex:
            self.__available_updates.clear()
            self.__lock.release()
            raise CheckUpdatesError("checking for updates failed - {}".format(ex))

    def run(self) -> None:
        while True:
            try:
                time.sleep(getDelay())
                logger.info("starting automatic update check ...")
                self.__checkUpdates()
            except Exception as ex:
                logger.error("automatic update check failed - {}".format(ex))

    def getAvailableUpdates(self, refresh: bool = False) -> dict:
        if self.__lock.locked():
            raise UpdateCheckInProgress("currently checking for updates")
        else:
            if refresh:
                self.__checkUpdates()
            return self.__available_updates

    def update(self, image: str):
        if self.__lock.locked():
            raise UpdateCheckInProgress("currently checking for updates")
        else:
            if image not in self.__available_updates:
                raise NotFound("no update for '{}' available".format(image))
            repo, tag = image.rsplit(":", 1)
            if "/" in tag:
                raise ValueError("no image tag provided")
            resp = requests.post(
                url="{}/{}".format(conf.DeploymentManager.url, conf.DeploymentManager.img_api),
                json={"repository": repo, "tag": tag}
            )
            if resp.ok:
                if self.__available_updates[image][model.Update.type] == model.UpdateType.core:
                    self.__updateCore(image)
                elif self.__available_updates[image][model.Update.type] == model.UpdateType.protocol_adapter:
                    self.__updateProtocolAdapter(image)
                elif self.__available_updates[image][model.Update.type] == model.UpdateType.worker:
                    self.__updateWorker(image)
                del self.__available_updates[image]
            else:
                raise UpdateError("updating '{}' failed - {}".format(image, resp.status_code))
