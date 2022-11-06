from pysnmp import hlapi

class PowerSNMP:
    def __init__(self, ip: str, user: str):
        self._ip = ip
        self._creds = hlapi.UsmUserData(user, authProtocol=hlapi.usmNoAuthProtocol, privProtocol=hlapi.usmNoPrivProtocol)
        self._engine = hlapi.SnmpEngine()
        self._transport = hlapi.UdpTransportTarget((self._ip, 161), timeout=10)
        self._datacontext = hlapi.ContextData()

    def get(self, oid) -> dict:
        handler = hlapi.getCmd(
            self._engine,
            self._creds,
            self._transport,
            self._datacontext,
            hlapi.ObjectType(hlapi.ObjectIdentity(oid))
        )
        return self.fetch(handler, 1)[0]

    def set(self, oid, new_value):
        handler = hlapi.setCmd(
            self._engine,
            self._creds,
            self._transport,
            self._datacontext,
            hlapi.ObjectType(hlapi.ObjectIdentity(oid), hlapi.Integer(new_value))
        )
        return self.fetch(handler, 1)[0]

    def fetch(self, handler, count):
        result = []
        for i in range(count):
            try:
                error_indication, error_status, error_index, var_binds = next(handler)
                if not error_indication and not error_status:
                    items = {}
                    for var_bind in var_binds:
                        items[str(var_bind[0])] = self.cast(var_bind[1])
                    result.append(items)
                else:
                    raise RuntimeError(f'got SNMP error: {error_indication}, {error_status}')
            except StopIteration:
                break
        return result

    def cast(self, value):
        try:
            return int(value)
        except (ValueError, TypeError):
            try:
                return float(value)
            except (ValueError, TypeError):
                try:
                    return str(value)
                except (ValueError, TypeError):
                    pass
        return value

# Load1 State = 1.3.6.1.4.1.850.1.1.3.2.3.3.1.1.4.1.1
# Load1 Command = 1.3.6.1.4.1.850.1.1.3.2.3.3.1.1.6.1.1
# Load2 State = 1.3.6.1.4.1.850.1.1.3.2.3.3.1.1.4.1.2
# Load2 Command = 1.3.6.1.4.1.850.1.1.3.2.3.3.1.1.6.2
# See https://assets.tripplite.com/flyer/supported-snmp-oids-technical-application-bulletin-en.pdf
# 1 = off
# 2 = on