table=[{"d":1,"b":2,"c":3,"a":5, "e":6, "f":7},{"d":4, "b":5, "c":6, "a":'ddd', "e": 'aaa', 'f': 'ddd'}]
grouping={"first":[1,2], "second":[6]}
#grouping={}

from functools import reduce
from bs4 import BeautifulSoup
from json2html import json2html

out=json2html.convert(table)
soup=BeautifulSoup(out,"html.parser")

l=[]
if len(grouping):
	l=(list(reduce(lambda x,y: x+y,  list(grouping.values()))))	


ths=soup.findAll("th")

newtr="<tr>"
for each in grouping:
	group=grouping[each]
	groups=[]
	
	ths[group[0]-1]['colspan']=len(group)
	ths[group[0]-1].string=each
	
	for e in group[1:]:
		ths[e-1].extract()

	for e in group:
		groups.append(list(table[0].keys())[e-1])
	for e in groups:
		newtr+="<th>"+e+"</th>"
	
newtr+="</tr>"

for th in ths:
	if not th.get('colspan', None):
		th['rowspan']=2

newtr=BeautifulSoup(newtr, "html.parser")

thead=soup.find('thead')
thead.append(newtr)

print(soup)
