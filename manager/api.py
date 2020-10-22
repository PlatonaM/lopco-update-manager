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

__all__ = ("Updates", "Update")


from .logger import getLogger
from .updater import Updater, UpdateCheckInProgress
import falcon
import json


logger = getLogger(__name__.split(".", 1)[-1])


def reqDebugLog(req):
    logger.debug("method='{}' path='{}' content_type='{}'".format(req.method, req.path, req.content_type))

def reqErrorLog(req, ex):
    logger.error("method='{}' path='{}' - {}".format(req.method, req.path, ex))


class BadRequest(Exception):
    pass


class Updates:
    def __init__(self, updater: Updater):
        self.__updater = updater

    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response):
        reqDebugLog(req)
        try:
            if req.params:
                if "refresh" in req.params and req.params["refresh"] == "true":
                    resp.body = json.dumps(self.__updater.getAvailableUpdates(refresh=True))
                else:
                    raise BadRequest("unknown parameters or values - {}".format(req.params))
            else:
                resp.body = json.dumps(self.__updater.getAvailableUpdates())
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except BadRequest as ex:
            resp.status = falcon.HTTP_400
            reqErrorLog(req, ex)
        except UpdateCheckInProgress as ex:
            resp.status = falcon.HTTP_503
            reqErrorLog(req, ex)
        except Exception as ex:
            resp.status = falcon.HTTP_500
            reqErrorLog(req, ex)
