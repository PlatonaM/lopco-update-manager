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


__all__ = ("Update", "UpdateType", "Entity")


class Update:
    type = "type"
    entities = "entities"
    time = "time"


class UpdateType:
    core = "core"
    worker = "worker"
    protocol_adapter = "protocol-adapter"


class Entity:
    name = "name"


class Container:
    labels = "labels"
    ports = "ports"
    environment = "environment"


class CLabels:
    lopco_id = "lopco-id"
    lopco_type = "lopco-type"


class Deployment:
    id = "id"
    type = "type"
    ports = "ports"
    configs = "configs"


class ProtoAdapter:
    name = "name"
    description = "description"
    ports = "ports"


class PAPorts:
    port = "port"
    protocol = "protocol"
