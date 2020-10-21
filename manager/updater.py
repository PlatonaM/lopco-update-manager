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


__all__ = ("Updater", )


from . import model
from .logger import getLogger
from .configuration import conf
from .util import getDelay
import threading
import requests
import time
import json


logger = getLogger(__name__.split(".", 1)[-1])


class CheckUpdateError(Exception):
    pass


class Updater(threading.Thread):
    def __init__(self):
        super().__init__(name="updater", daemon=True)
        self.available_updates = dict()

    def __checkUpdate(self, image: str) -> bool:
        try:
            resp = requests.get(
                url="{}/{}/{}".format(
                    conf.DeploymentManager.url,
                    conf.DeploymentManager.img_api,
                    image.replace("/", "%252F")
                )
            )
            if resp.ok:
                image_digests = resp.json()["digests"]
                image_digests = ",".join(image_digests)
                resp = requests.get(
                    url="{}/{}/{}".format(
                        conf.DeploymentManager.url,
                        conf.DeploymentManager.dig_api,
                        image.replace("/", "%252F")
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
        except Exception as ex:
            raise CheckUpdateError(ex)

    def __checkCoreImages(self):
        images = conf.Core.images.split(";")
        for image in images:
            try:
                if self.__checkUpdate(image):
                    if image not in self.available_updates:
                        self.available_updates[image] = {
                            model.Update.type: model.UpdateType.core,
                            model.Update.entities: dict()
                        }
                else:
                    if image in self.available_updates:
                        del self.available_updates[image]
            except CheckUpdateError as ex:
                logger.warning("update check for '{}' failed - {}".format(image, ex))

    def __checkUserImages(self, url: str, type: str):
        resp = requests.get(url=url)
        if resp.ok:
            for key, value in resp.json().items():
                value = json.loads(value)
                image = value["image"]
                try:
                    logger.debug(image)
                    if self.__checkUpdate(image):
                        if image not in self.available_updates:
                            self.available_updates[image] = {
                                model.Update.type: type,
                                model.Update.entities: {key: {model.Entity.name: value["name"]}}
                            }
                        else:
                            if key not in self.available_updates[image][model.Update.entities]:
                                self.available_updates[image][model.Update.entities][key] = {
                                    model.Entity.name: value["name"]
                                }
                    else:
                        if image in self.available_updates:
                            del self.available_updates[image]
                except CheckUpdateError as ex:
                    logger.warning("update check for '{}' failed - {}".format(image, ex))

    def run(self) -> None:
        while True:
            time.sleep(getDelay())
            try:
                self.__checkCoreImages()
                self.__checkUserImages(
                    "{}/{}".format(conf.ProtocolAdapterRegistry.url, conf.ProtocolAdapterRegistry.api),
                    model.UpdateType.protocol_adapter
                )
                self.__checkUserImages(
                    "{}/{}".format(conf.WorkerRegistry.url, conf.WorkerRegistry.api),
                    model.UpdateType.worker
                )
                logger.debug(self.available_updates)
            except Exception as ex:
                logger.exception("error during update check:".format(ex))
