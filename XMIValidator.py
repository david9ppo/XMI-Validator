import sys, re
from xml.dom.minidom import *

class XMIValidator:
	"""docstring for ClassName"""
	def __init__(self, xmi):
		self.dom = parse(xmi)
		self.entNames=self.loadEntityNamesInList()
		self.attrEntModel=self.loadEntitiesAttributes()
		self.relEntModel=self.loadEntitiesRelationships()


	def loadEntitiesAttributes(self):
		entDict={}
		entities = self.dom.getElementsByTagName("entities")
		for entity in entities:
			entDict[entity.getAttribute("entityName")]=self.getAttributesFromEntity(entity)
		return entDict

	def loadEntityNamesInList(self):
		names=[]
		entities = self.dom.getElementsByTagName("entities")
		for entity in entities:
			names.append(entity.getAttribute("entityName"))
		return names

	def getEntityNameByPos(self, index):
		return self.entNames[index]

	def getEntityNames(self):
		return self.entNames

	def loadEntitiesRelationships(self):
		entDict={}
		entities = self.dom.getElementsByTagName("entities")
		for entity in entities:
			entDict[entity.getAttribute("entityName")]=self.getRelationshipsFromEntity(entity)
		return entDict

	def extractPosPojo(self, pojoString):
		return int(re.findall("[0-9]+", pojoString)[0])

	def searchOrphanPojos(self):
		errors=[]
		nameDtos=[]
		dtos=self.dom.getElementsByTagName("dtos")
		numDtos=len(dtos)
		for d in dtos:
			nameDtos.append(d.getAttribute("dtoName"))
		uses=[0]*numDtos
		queries=self.dom.getElementsByTagName("queries")
		for q in queries:
			retType=q.getElementsByTagName("return")
			pojo=retType[0].getAttribute("dto")
			if(pojo!=""):
				#extraer posicion del dto y aumentar uso
				pos=self.extractPosPojo(pojo)
				uses[pos]+=1
		# recorrer vector en busca de alguno con 0
		inusabled=[]
		for idx,val in enumerate(uses):
			if(val==0):
				inusabled.append(idx)
		#sacar nombre de los no usados
		for p in inusabled:
			errors.append(nameDtos[p]+' con posicion @dtos.'+str(p))
		return errors

	def checkWrongTypesInPojos(self):
		errors=[]
		dtos=self.dom.getElementsByTagName("dtos")
		for dto in dtos:
			attributes=dto.getElementsByTagName("attribtesDTOs")
			for attr in attributes:
				name=attr.getAttribute("attributeName")
				type=attr.getAttribute("type")
				# validar campos id de tipo Long
				if(name.startswith("id") or name.startswith("Id") or name.endswith("id") or name.endswith("Id")):
					if(not(self.searchWordInText("Long",type))):
						#añadir error
						if(type==""):
							type="String"
						errors.append("Atributo "+name+" del POJO "+dto.getAttribute("dtoName")+" no es de tipo Long. Es de tipo "+type+" .¿Es correcto?")
				elif(self.searchWordInText("name",name) or self.searchWordInText("Name",name) or self.searchWordInText("Na",name)):
					if(not type==""):
						#añadir error
						errors.append("Atributo "+name+" del POJO "+dto.getAttribute("dtoName")+" no es de tipo String.")
				elif(self.searchWordInText("descrip",name) or self.searchWordInText("Ds",name)):
					if(not type==""):
						#añadir error
						errors.append("Atributo "+name+" del POJO "+dto.getAttribute("dtoName")+" no es de tipo String.")
				elif(self.searchWordInText("date",name) or self.searchWordInText("Date",name)):
					if(not(self.searchWordInText("Date",type))):
						#añadir error
						errors.append("Atributo "+name+" del POJO "+dto.getAttribute("dtoName")+" no es de tipo Date.")
		return errors

	def getDAOName(self):
		model=self.dom.getElementsByTagName("geniee:Model")
		return model[0].getAttribute("modelName")

	def getAttributesFromEntity(self,entity):
		attrList=[]
		attributes=entity.getElementsByTagName("attributes")
		for at in attributes:
			attrList.append(at.getAttribute("attributeName"))
		return attrList

	def extractPosEntity(self, string):
		return re.search('@entities.[0-9]+', string).group(0).split(".")[1]

	def getRelationshipsFromEntity(self,entity):
		relList=[]
		rels=entity.getElementsByTagName("relationships")
		for r in rels:
			cadena=r.getAttribute("endRelationShip")
			pos=int(self.extractPosEntity(cadena))
			relList.append(self.getEntityNameByPos(pos))
		return relList

	def checkDuplicatedRepositories(self):
		errors=[]
		repoSet = set()
		repos = self.dom.getElementsByTagName("repositories")
		#cargar primer repo
		repoSet.add(repos[0].getAttribute("repositoryName"))
		self.checkDuplicatedQueriesInRepo(repos[0])
		for repo in repos[1:]:
			if repo.getAttribute("repositoryName") in repoSet:
				errors.append('Repositorio repetido: '+repo.getAttribute("repositoryName"))
			else:
				self.checkDuplicatedQueriesInRepo(repo)
				repoSet.add(repo.getAttribute("repositoryName"))
		return errors
		
	def checkDuplicatedQueriesInRepo(self,repo):
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

	def checkRuleMethods(self):
		errors=[]
		queries=self.dom.getElementsByTagName("queries")
		for q in queries:
			if(q.getAttribute("queryName").find("Rule") > -1):
				# metodo de reglas
				p=q.getElementsByTagName("parameters")
				cont=0
				for param in p:
					if(param.getAttribute("parameterName").find("Event")> -1 or param.getAttribute("parameterName").find("event")> -1):
						cont+=1
				if cont!=1:
					errors.append('Metodo de reglas '+q.getAttribute("queryName")+' no tiene parametro de entrada ruleEvent')
				retType=q.getElementsByTagName("return")
				if(retType[0].getAttribute("type").find("BigDecimal")==-1):
					errors.append('Metodo de reglas '+q.getAttribute("queryName")+' no devuelve parámetro de tipo BigDecimal')
		return errors

	def checkCatTextMethods(self):
		errors=[]
		queries=self.dom.getElementsByTagName("queries")
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

	def checkParametersType(self):
		errors=[]
		queries=self.dom.getElementsByTagName("queries")
		for q in queries:
			p=q.getElementsByTagName("parameters")
			for param in p:
				if(param.getAttribute("parameterName").find("id")> -1 or param.getAttribute("parameterName").find("Id")> -1):
					typ=param.getAttribute("type")
					if(typ.find("Long")==-1):
						if(typ==""):
							typ="String"
						errors.append('Parametro '+param.getAttribute("parameterName")+' del metodo '+q.getAttribute("queryName")+ ' no es de tipo Long. Es de tipo '+typ+'. ¿Es correcto?')
				elif(param.getAttribute("parameterName").find("queryDate")> -1 or param.getAttribute("parameterName").find("Date")> -1):
					typ=param.getAttribute("type")
					if(typ.find("Date")==-1):
						if(typ==""):
							typ="String"
						errors.append('Parametro '+param.getAttribute("parameterName")+' del metodo '+q.getAttribute("queryName")+ ' no es de tipo Date. Es de tipo '+typ+'. ¿Es correcto?')

		return errors

	def checkDTDDocumentation(self):
		errors=[]
		queries=self.dom.getElementsByTagName("queries")
		for q in queries:
			p=q.getAttribute("dtdDocumentation")
			if(p==""):
				errors.append(q.getAttribute("queryName"))
		return errors

	def findEntitiesAndFieldsInDTDDoc(self,dtdDoc):
		# l=[]
		# dtdDoc="\n".join(dtdDoc.splitlines())
		entAndFields=re.findall("[a-zA-Z]{12,}"'\.'"[a-zA-Z]+", dtdDoc)
		out=[]
		for eF in entAndFields:
			capiteF=eF[0].upper()+eF[1:]
			out.append(capiteF)
		return out

	def extractEntitiesFromJoins(self,dtdDoc):
		lista=[]
		#extraer INNER JOINS
		cadena=re.findall('[a-zA-Z]{12,} +INNER +JOIN +[a-zA-Z]+', dtdDoc)
		for c in cadena:
			lista.append(re.sub('\s+',"#",c).split("#"))
		#extraer LEFT JOINS
		cadena=re.findall('[a-zA-Z]{12,} +LEFT +JOIN +[a-zA-Z]+', dtdDoc)
		for c in cadena:
			lista.append(re.sub('\s+',"#",c).split("#"))
		#extraer entidad1 (as xxx) y entidad2
		cadena=re.findall('[a-zA-Z]{12,} +y +[a-zA-Z]{12,}', dtdDoc)
		for c in cadena:
			lista.append(re.sub('\s+',"#",c).split("#"))
		return lista

	def checkValidityEntitiesJoins(self):
		warnings=[]
		queries=self.dom.getElementsByTagName("queries")
		for q in queries:
			dtdDoc=q.getAttribute("dtdDocumentation")
			joins=self.extractEntitiesFromJoins(dtdDoc)
			for j in joins: # entIzq INNER JOIN entDer o entIzq LEFT JOIN entDer o entIzq y entDer
				entIzq=j[0]
				entDer=j[-1]
				if(entIzq not in self.attrEntModel):
					 warnings.append('Metodo: '+ q.getAttribute("queryName")+' #Entidad '+entIzq+' usada en la parte IZQUIERDA de una JOIN no existe o tiene un nombre distinto en el modelo.')
				if(entDer not in self.attrEntModel):
					 warnings.append('Metodo: '+ q.getAttribute("queryName")+' #Entidad '+entDer+' usada en la parte DERECHA de una JOIN no existe o tiene un nombre distinto en el modelo.')
				entIzqNew=entIzq[0].upper()+entIzq[1:]
				entDerNew=entDer[0].upper()+entDer[1:]
				# verifica si es posible por modelo la JOIN entre entIzq y entDer
				# print(entDer)
				# si existe la entDerNew, miro si se puede hacer la JOIN
				if(entDerNew in self.relEntModel.keys()):
				 	if(entIzqNew not in self.relEntModel[entDerNew]):
				 		warnings.append('Metodo: '+ q.getAttribute("queryName")+' #No es posible por modelo hacer una JOIN entre '+entIzq+' y '+entDer+' .')
			return warnings

	def checkWrongEntities(self):
		errors=set()
		queries=self.dom.getElementsByTagName("queries")
		for q in queries:
			dtdDoc=q.getAttribute("dtdDocumentation")
			entFields=self.findEntitiesAndFieldsInDTDDoc(dtdDoc)
			for filtro in entFields:
				entidad=filtro.split(".")[0]
				campo=filtro.split(".")[1]
				campo=campo[0].lower()+campo[1:]
				#comprobar que la entidad existe
				if(entidad not in self.attrEntModel):
					 errors.add('Metodo: '+ q.getAttribute("queryName")+' #Entidad '+entidad+' que se usa en los filtros no existe o tiene un nombre distinto en el modelo.')
				else: #entidad existe, comprobar que el campo es de esa entidad
					if(campo not in self.attrEntModel[entidad]):
						errors.add('Metodo: '+q.getAttribute("queryName")+' #Campo '+campo+' de la entidad '+entidad+' que aparece como filtro no se encuentra como atributo de esa entidad en el modelo.')

			# 	# indexesINNER = [i for i,x in enumerate(l) if x == "INNER"]
			# 	# for ind in indexesINNER:
			# 		# if(len(l[ind-1])>5):
			# 			# print(l[ind-1])
			# 	# indexesJOIN = [i for i,x in enumerate(l) if x == "JOIN"]
			# 	# for ind in indexesJOIN:
			# 		# if(len(l[ind+1])>5):
			# 			# print(l[ind+1])
		return sorted(errors)

	def searchWordInText(self,word, text):
		results=re.findall(word, text)
		if(results==[]):
			return False
		return True

	def checkKeywordsInDoc(self):
		errors=[]
		queries=self.dom.getElementsByTagName("queries")
		for q in queries:
			qDateKW=False
			listaKW=False
			#idKW=False

			dtdDoc=q.getAttribute("dtdDocumentation")
			param=q.getElementsByTagName("parameters")
			if(self.searchWordInText("queryDate",dtdDoc)):
				qDateKW=True
			if(self.searchWordInText("lista",dtdDoc)):
				listaKW=True
			# if(searchWordInText("id",dtdDoc)):
			# 	idKW=True

			#Comprobar queryDate en DOC y que esté como parametro entrada
			if(qDateKW):
				paramQueryDate=False
				for p in param:
					if(p.getAttribute("parameterName").find("queryDate")> -1 or p.getAttribute("parameterName").find("Date")> -1 or p.getAttribute("parameterName").find("querydate")> -1):
						paramQueryDate=True
				if(not paramQueryDate): ##queryDate en doc pero no como parametro
					errors.append('En la DOC del metodo '+q.getAttribute("queryName")+' se hace referencia a un queryDate que no aparece como parámetro de entrada')
			#Comprobar lista en DOC y que devuelva Colecction or Collection
			if(listaKW):
				retType=q.getElementsByTagName("return")
				if(not self.searchWordInText("Colecction",retType[0].getAttribute("xsi:type")) and not self.searchWordInText("Collection",retType[0].getAttribute("xsi:type"))):
					errors.append('En la DOC del metodo '+q.getAttribute("queryName")+' aparece "lista" y el metodo no devuelve una lista de elementos')
		return errors

	def solve(self):
		name=self.getDAOName()
		f = open('Informe_'+name+'.txt', 'w')
		f.write('**********************************************************'+'\n')
		f.write('Validaciones del DAO '+self.getDAOName()+'\n')
		f.write('**********************************************************'+'\n\n')
		f.write("Chequeando repositorios y metodos duplicados..."+'\n')
		f.write("==============================================="+'\n')
		e=self.checkDuplicatedRepositories()
		if(e==[]):
			f.write("OK"+'\n')
		else:
			for error in e:
				f.write(error+'\n')
		f.write('\n\n'+"Chequeando parametros en metodos de reglas..."+'\n')
		f.write("============================================="+'\n')
		e=self.checkRuleMethods()
		if(e==[]):
			f.write("OK"+'\n')
		else:
			for error in e:
				f.write(error+'\n')
		f.write('\n\n'+"Chequeando tipos de parametros..."+'\n')
		f.write("================================="+'\n')
		e=self.checkParametersType()
		if(e==[]):
			f.write("OK"+'\n')
		else:
			for error in e:
				f.write(error+'\n')
		f.write('\n\n'+"Chequeando metodos sin Documentacion..."+'\n')
		f.write("======================================="+'\n')
		e=self.checkDTDDocumentation()
		if(e==[]):
			f.write("OK"+'\n')
		else:
			for error in e:
				f.write(error+'\n')
		f.write('\n\n'+"Chequeando entidad.campo en las consultas..."+'\n')
		f.write("======================================="+'\n')
		e=self.checkWrongEntities()
		if(len(e)==0):
			f.write("OK"+'\n')
		else:
			for error in e:
				f.write(error+'\n')
		f.write('\n\n'+"Chequeando metodos CatalogText..."+'\n')
		f.write("======================================="+'\n')
		e=self.checkCatTextMethods()
		if(e==[]):
			f.write("OK"+'\n')
		else:
			for error in e:
				f.write(error+'\n')
		f.write('\n\n'+"Chequeando filtros en la DOC que no aparecen como parámetros de entrada..."+'\n')
		f.write("======================================="+'\n')
		e=self.checkKeywordsInDoc()
		if(e==[]):
			f.write("OK"+'\n')
		else:
			for error in e:
				f.write(error+'\n')
		f.write('\n\n'+"POJOS no devueltos en ningun metodo:"+'\n')
		f.write("======================================="+'\n')
		e=self.searchOrphanPojos()
		if(e==[]):
			f.write("OK"+'\n')
		else:
			for error in e:
				f.write(error+'\n')
		f.write('\n\n'+"Comprobando tipos en atributos de los POJOS..."+'\n')
		f.write("======================================="+'\n')
		e=self.checkWrongTypesInPojos()
		if(e==[]):
			f.write("OK"+'\n')
		else:
			for error in e:
				f.write(error+'\n')
		f.write('\n\n'+"Comprobando validez de las JOINS..."+'\n')
		f.write("======================================="+'\n')
		e=self.checkValidityEntitiesJoins()
		if(e==[]):
			f.write("OK"+'\n')
		else:
			for error in e:
				f.write(error+'\n')
		print("Validacion acabada")
		f.close()


if(len(sys.argv)<2):
	raise ValueError('Se debe introducir al menos un fichero XMI para validar.')
else:
	for doc in sys.argv[1:]:
		if not doc.endswith('.xmi'):
			raise ValueError('El parámetro no es un fichero XMI')
		a=XMIValidator(doc).solve()