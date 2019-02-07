import sys
import myst as stringtemplate

st = stringtemplate.StringTemplateGroup('mygroup', 'templates')

begin = int(sys.argv[1])
end = int(sys.argv[2])

for i in range(begin, end+1):
	xml = st.getInstanceOf('mcvmxml')

	xml['num'] = '%03d' % i
	xml['hex'] = '%02x' % i

	filename = 'mcvm%03d.xml' % i
	f = open(filename, 'w')
	print >> f, xml 
	f.close()
