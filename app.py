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

from manager.logger import initLogger, getLogger
from manager.configuration import conf
from manager.updater import Updater
from manager import api
import falcon


initLogger(conf.Logger.level)

updater = Updater()

if conf.Update.automatic:
    updater.start()

app = falcon.API()

app.req_options.strip_url_path_trailing_slash = True

routes = (
    ("/updates", api.Updates(updater)),
    ("/updates/{update}", api.Update(updater))
)

for route in routes:
    app.add_route(*route)

# gunicorn -b 0.0.0.0:8080 --workers 2 --threads 4 --worker-class gthread --log-level error app:app
