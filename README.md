#### /updates

**GET**

_List available updates._

    # Example
    
    curl http://<host>/updates
    {
        "platonam/lopco-deployment-manager:dev": {
            "type": "core",
            "entities": [],
            "time": "2020-11-20T10:10:01.015774Z"
        }
    }

_Check for updates and list available._

    # Example
    
    curl http://<host>/updates?refresh=true
    {
        "platonam/lopco-deployment-manager:dev": {
            "type": "core",
            "entities": [],
            "time": "2020-11-20T12:29:43.695613Z"
        },
        "platonam/lopco-http-protocol-adapter:dev": {
            "type": "protocol-adapter",
            "entities": [
                "5e674298-49d5-4723-926c-cf062dd9c141"
            ],
            "time": "2020-11-20T12:29:52.005179Z"
        }
    }

#### /updates/{update}

**PATCH**

    # Example

    curl -X PATCH http://<host>/updates/platonam%2Flopco-http-protocol-adapter%3Adev
