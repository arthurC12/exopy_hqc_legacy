from exopy_hqc_legacy.instruments.drivers.visa.qdac2 import QDac2, QDac2SingleChannel
from exopy_hqc_legacy.instruments.drivers.visa.holzworth_hsx9000 import Holzworth9000


connection_info = {'resource_name':'TCPIP0::169.254.1.1::5025::SOCKET'}
connection_info_hw = {'resource_name': 'TCPIP0::169.254.117.11::9760::SOCKET'}
# print(connection_info['resource_name'])
qdac= QDac2(connection_info)
hw = Holzworth9000(connection_info_hw)


hwch02 = hw.get_channel(2)
ch18 = qdac.get_channel(18)

#%%%%%
import pyvisa as visa
rm = visa.ResourceManager('@py')
qdac = rm.open_resource('TCPIP0::169.254.1.1::5025::SOCKET')
qdac.read_termination = '\n'
qdac.write_termination = '\n'
print(qdac.query("*IDN?"))
# qdac.write("sour9:filt high")
print(qdac.query("SOUR9:FILT?"))
qdac.close()
