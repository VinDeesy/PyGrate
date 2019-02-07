import re

class StringTemplateGroup:
	def __init__(self, name, dir):
		self.name = name
		self.dir = dir

	def getInstanceOf(self, name):
		f = open(self.dir + '/' + name + '.st')
		return StringTemplate(f.read(), self)

class StringTemplate:
	def __init__(self, template, group):
		self.group = group
		self.template = template
		self.dict = {}

		funcs = re.findall('\$.+?\(\)\$', self.template)
		funcs = [f.strip('$') for f in funcs]

		for f in funcs:
			t = self.group.getInstanceOf(f.strip('()'))
			#self[f] = t
			p = '\$'+f+'\$'
			p = re.sub('\(', '\\\(', p)
			p = re.sub('\)', '\\\)', p)
			self.template = re.sub(p, t.template, self.template)

	def __setitem__(self, key, item):
		try:
			self.dict[key]
		except KeyError:
			self.dict[key] = []
		#print key, '-->', item.__class__
		if item: self.dict[key].append(str(item))

	def __str__(self):
		rv = self.template
		for k in self.dict.keys():
			p = '\$'+k+'\$'
			p = re.sub('\(', '\\\(', p)
			p = re.sub('\)', '\\\)', p)
			#print p, 'FOUND: ', re.findall(p, rv)
			for v in self.dict[k]:
				rv = re.sub(p, v+'$'+k+'$', rv)
			rv = re.sub(p, '', rv)
		toks = re.findall('\$.+?\$', rv)
		for t in toks:
			t = re.sub('\$', '\\\$', t)
			rv = re.sub(t, '', rv)
		return rv

