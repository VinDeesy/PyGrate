import sys
import myst as stringtemplate

st = stringtemplate.StringTemplateGroup('mygroup', 'templates')

begin = int(sys.argv[1])
end = int(sys.argv[2])

for i in range(begin, end+1):
	dhcp = st.getInstanceOf('dhcp')

	dhcp['num'] = '%03d' % i
	dhcp['hex'] = '%02x' % i
	dhcp['ip']  = '%d' % (i + 80)

	print dhcp
