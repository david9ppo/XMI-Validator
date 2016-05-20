import sys
from xml.dom.minidom import *

if(len(sys.argv)!=2):
	raise ValueError('Se debe introducir un solo fichero para validar.')
else:
	doc=sys.argv[1]
	if not doc.endswith('.xmi'):
		raise ValueError('El parámetro no es un fichero XMI')

dom=parse(doc)

def loadEntities(xmi):
	entDict={}
	entities = xmi.getElementsByTagName("entities")
	for entity in entities:
		entDict[entity.getAttribute("entityName")]=getAttributesFromEntity(entity)
	return entDict

def viewMap(map):
	for k, v in map.items():
		print(k, v)
	
def getDAOName(xmi):
	model=xmi.getElementsByTagName("geniee:Model")
	return model[0].getAttribute("modelName")

def getAttributesFromEntity(entity):
	attrList=[]
	attributes=entity.getElementsByTagName("attributes")
	for at in attributes:
		attrList.append(at.getAttribute("attributeName"))
	return attrList
	
def checkDuplicatedRepositories(xmi):
	errors=[]
	repoSet = set()
	repos = xmi.getElementsByTagName("repositories")
	#cargar primer repo
	repoSet.add(repos[0].getAttribute("repositoryName"))
	checkDuplicatedQueriesInRepo(repos[0])
	for repo in repos[1:]:
		if repo.getAttribute("repositoryName") in repoSet:
			errors.append('Repositorio repetido: '+repo.getAttribute("repositoryName"))
		else:
			checkDuplicatedQueriesInRepo(repo)
			repoSet.add(repo.getAttribute("repositoryName"))
	return errors
	
def checkDuplicatedQueriesInRepo(repo):
	errors=[]
	qSet=set()
	queries=repo.getElementsByTagName("queries")
	#Comprobar que al menos tiene un metodo
	if len(queries) <1:
		errors.append('El repositorio '+repo.getAttribute("repositoryName")+' no tiene queries definidas')
	else:
		#cargar primera query
		qSet.add(queries[0].getAttribute("queryName"))
		for q in queries[1:]:
			if q.getAttribute("queryName") in qSet:
				errors.append('Metodo '+q.getAttribute("queryName")+' duplicado en repositorio '+repo.getAttribute("repositoryName"))
			else:
				qSet.add(q.getAttribute("queryName"))
	return errors

def checkRuleMethods(xmi):
	errors=[]
	queries=xmi.getElementsByTagName("queries")
	for q in queries:
		if(q.getAttribute("queryName").find("Rule") > -1):
			# metodo de reglas
			#print(q.getAttribute("queryName"))
			p=q.getElementsByTagName("parameters")
			#chequear 3 parametros (id, qDate y ruleEvent)
			#if(len(p)!=3):
			#	raise ValueError('Metodo de reglas '+q.getAttribute("queryName")+' no tiene 3 parametros de entrada')
			cont=0
			for param in p:
				if(param.getAttribute("parameterName").find("Event")> -1):
					cont+=1
			if cont!=1:
				errors.append('Metodo de reglas '+q.getAttribute("queryName")+' no tiene parametro de entrada ruleEvent')
			retType=q.getElementsByTagName("return")#.getAttribute("type")
			if(retType[0].getAttribute("type").find("BigDecimal")==-1):
				errors.append('Metodo de reglas '+q.getAttribute("queryName")+' no devuelve parámetro de tipo BigDecimal')
	return errors
	
def checkCatTextMethods(xmi):
	errors=[]
	queries=xmi.getElementsByTagName("queries")
	for q in queries:
		if(q.getAttribute("queryName").find("getCatalogText") > -1 or q.getAttribute("queryName").find("findCatalogText") > -1):
			# metodo de reglas
			p=q.getElementsByTagName("parameters")
			filters=set()
			for param in p:
				if(param.getAttribute("parameterName").lower().find("use")> -1):
					filters.add("use")
					# #validar tipo
					if(param.getAttribute("type").find("Long")==-1):
						#error, filtro CatText no es Long
						errors.append('El parámetro '+param.getAttribute("parameterName")+' del metodo '+q.getAttribute("queryName")+' no es de tipo Long')
				elif(param.getAttribute("parameterName").lower().find("type")> -1):
					filters.add("type")
					#validarTipo
					if(param.getAttribute("type").find("Long")==-1):
						#error, filtro CatText no es Long
						errors.append('El parámetro '+param.getAttribute("parameterName")+' del metodo '+q.getAttribute("queryName")+' no es de tipo Long')
				elif(param.getAttribute("parameterName").lower().find("media")> -1):
					filters.add("media")
					#validarTipo
					if(param.getAttribute("type").find("Long")==-1):
						#error, filtro CatText no es Long
						errors.append('El parámetro '+param.getAttribute("parameterName")+' del metodo '+q.getAttribute("queryName")+' no es de tipo Long')
			if(len(filters)!=3):
				errors.append('Falta al menos uno de los 3 filtros del CatalogText como parámetros de entrada en el metodo '+q.getAttribute("queryName"))
	return errors

def checkParametersType(xmi):
	errors=[]
	queries=xmi.getElementsByTagName("queries")
	for q in queries:
		p=q.getElementsByTagName("parameters")
		for param in p:
			if(param.getAttribute("parameterName").find("id")> -1 or param.getAttribute("parameterName").find("Id")> -1):
				typ=param.getAttribute("type")
				if(typ.find("Long")==-1):
					errors.append('Parametro '+param.getAttribute("parameterName")+' del metodo '+q.getAttribute("queryName")+ ' no es de tipo Long')
			elif(param.getAttribute("parameterName").find("queryDate")> -1 or param.getAttribute("parameterName").find("Date")> -1):
				typ=param.getAttribute("type")
				if(typ.find("Date")==-1):
					errors.append('Parametro '+param.getAttribute("parameterName")+' del metodo '+q.getAttribute("queryName")+ ' no es de tipo Date')

	return errors

def checkDTDDocumentation(xmi):
	errors=[]
	queries=xmi.getElementsByTagName("queries")
	for q in queries:
		p=q.getAttribute("dtdDocumentation")
		if(p==""):
			errors.append(q.getAttribute("queryName"))
	return errors

def tratarTexto(dtdDoc):
	l=[]
	dtdDoc="\n".join(dtdDoc.splitlines())
	dtdDoc = dtdDoc.replace('\t','')
	dtdDoc = dtdDoc.replace(">="," ")
	dtdDoc = dtdDoc.replace("<="," ")
	dtdDoc = dtdDoc.replace("="," ")
	dtdDoc = dtdDoc.replace("min"," ")
	dtdDoc = dtdDoc.replace("max"," ")
	dtdDoc = dtdDoc.replace("List"," ")
	dtdDoc = dtdDoc.replace("list"," ")
	dtdDoc = dtdDoc.replace("<"," ")
	dtdDoc = dtdDoc.replace(">"," ")
	#quitar parentesis
	dtdDoc = dtdDoc.replace("("," ")
	dtdDoc = dtdDoc.replace(")"," ")
	if(dtdDoc!=""):
		l=dtdDoc.split('\n')
		l=list(filter(lambda x:x!='',l))
	return l


def checkWrongEntities(xmi):
	d=loadEntities(xmi)
	errors=[]
	queries=xmi.getElementsByTagName("queries")
	for q in queries:
		dtdDoc=q.getAttribute("dtdDocumentation")
		l=tratarTexto(dtdDoc)
		for linea in l:
			linea=linea.split(" ")
			for word in linea:
				if "." in word: # ENTIDAD.CAMPO
					#print(word) 
					entidad=word.split(".")[0]
					if(entidad!='' and len(entidad)>=12):
						entidad=entidad[0].upper()+entidad[1:]
						campo=word.split(".")[1]
						if(entidad not in d):
							errors.append('La entidad '+entidad+' que se usa en los filtros del metodo '+q.getAttribute("queryName")+' no existe o tiene un nombre distinto en el modelo')
						else: #si está
							if(len(campo)>2):
								if(campo not in d[entidad]):
									errors.append('El campo '+campo+' de la entidad '+entidad+' no se encuentra como atributo de esa entidad en el modelo')
									
						#print(entidad)
						#print(campo)
			# indexesINNER = [i for i,x in enumerate(l) if x == "INNER"]
			# for ind in indexesINNER:
				# if(len(l[ind-1])>5):
					# print(l[ind-1])
			# indexesJOIN = [i for i,x in enumerate(l) if x == "JOIN"]
			# for ind in indexesJOIN:
				# if(len(l[ind+1])>5):
					# print(l[ind+1])
	return errors

def searchWordInLine(word, line):
	if(word in line):
		return True
	return False

def checkKeywordsInDoc(xmi):
	errors=[]
	qDateKW=False
	idKW=False
	listaKW=False
	
	queries=xmi.getElementsByTagName("queries")
	for q in queries:
		dtdDoc=q.getAttribute("dtdDocumentation")
		param=q.getElementsByTagName("parameters")
		l=tratarTexto(dtdDoc)
		for linea in l:
			linea=linea.split(" ")
			if(searchWordInLine("queryDate",linea)):
				qDateKW=True
			if(searchWordInLine("id",linea)):
				idKW=True
			if(searchWordInLine("lista",linea)):
				listaKW=True
		#Dar errores si aplica
		if(qDateKW==True):
			paramQueryDate=False
			for p in param:
				if(p.getAttribute("parameterName").find("queryDate")> -1 or p.getAttribute("parameterName").find("Date")> -1):
					paramQueryDate=True
			if(paramQueryDate==False): ##queryDate en doc pero no como parametro
				errors.append('En la DOC del metodo '+q.getAttribute("queryName")+' se hace referencia a un queryDate que no aparece como parámetro de entrada')
	return errors
	
f = open('Informe.txt', 'w')
f.write('**********************************************************'+'\n')
f.write('Validaciones del DAO '+getDAOName(dom)+'\n')
f.write('**********************************************************'+'\n\n\n\n')
f.write("Chequeando repositorios y metodos duplicados..."+'\n')
f.write("==============================================="+'\n')
e=checkDuplicatedRepositories(dom)
for error in e:
	f.write(error+'\n')
f.write('\n\n'+"Chequeando parametros en metodos de reglas..."+'\n')
f.write("============================================="+'\n')
e=checkRuleMethods(dom)
for error in e:
	f.write(error+'\n')
f.write('\n\n'+"Chequeando tipos de parametros..."+'\n')
f.write("================================="+'\n')
e=checkParametersType(dom)
for error in e:
	f.write(error+'\n')
f.write('\n\n'+"Chequeando metodos sin Documentacion..."+'\n')
f.write("======================================="+'\n')
e=checkDTDDocumentation(dom)
for error in e:
	f.write(error+'\n')
f.write('\n\n'+"Chequeando entidad.campo en las consultas..."+'\n')
f.write("======================================="+'\n')
e=checkWrongEntities(dom)
for error in e:
	f.write(error+'\n')
f.write('\n\n'+"Chequeando metodos CatalogText..."+'\n')
f.write("======================================="+'\n')
e=checkCatTextMethods(dom)
for error in e:
	f.write(error+'\n')
f.write('\n\n'+"Chequeando filtros en la DOC que no aparecen como parámetros de entrada..."+'\n')
f.write("======================================="+'\n')
e=checkKeywordsInDoc(dom)
for error in e:
	f.write(error+'\n')
print("Validacion acabada")
f.close()
