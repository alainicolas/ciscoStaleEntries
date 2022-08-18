testbed:
  name: NXOS
  credentials:
    default:
      username: $device_username
      password: $device_password

devices:
  vps:
    os: linux
    type: linux
    credentials:
      default:
        username: $jumphost_username
    connections:
      cli:
        protocol: ssh
        ip: $jumphost_ip
{% for ip, id in list_ip_id %}
  NXOS_{{id}}:
    type: router
    os: nxos
    connections:
      vty:
        protocol: ssh
        ip: {{ip}}
        settings:
          GRACEFUL_DISCONNECT_WAIT_SEC: 0
          POST_DISCONNECT_WAIT_SEC: 0
          EXEC_TIMEOUT: 120
          CONFIG_TIMEOUT: 120
        port: 22
        proxy:
            - device: vps
{% endfor %}
