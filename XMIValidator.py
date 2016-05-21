import sys, re
from xml.dom.minidom import *

"""
Script que realiza validaciones sobre uno o más ficheros dao-XXX.xmi. Como resultado, se genera para cada uno de los ficheros
xmi de entrada un informe .txt.
"""

class XMIValidator:
	"""
	Clase que recibe y parsea el xmi y realiza validaciones para generar un informe con el resultado de estas.
	"""
	def __init__(self, xmi):
		self.dom = parse(xmi)
		self.entNames=self.loadEntityNamesInList()
		self.attrEntModel=self.loadEntitiesAttributes()
		self.relEntModel=self.loadEntitiesRelationships()

	def loadEntitiesAttributes(self):
		"""
        Método que crea y devuelve un diccionario:
            	- key: cada una de las entidades del modelo
            	- value: lista de atributos de la entidad
    	"""
		entDict={}
		entities = self.dom.getElementsByTagName("entities")
		for entity in entities:
			entDict[entity.getAttribute("entityName")]=self.getAttributesFromEntity(entity)
		return entDict

	def loadEntityNamesInList(self):
		"""
        Método que crea y devuelve una lista conteniendo
        el nombre (entityName) de cada entidad del modelo.
    	"""
		names=[]
		entities = self.dom.getElementsByTagName("entities")
		for entity in entities:
			names.append(entity.getAttribute("entityName"))
		return names

	def loadEntitiesRelationships(self):
		"""
        Método que crea y devuelve un diccionario:
            	- key: cada una de las entidades del modelo
            	- value: lista con los nombres de las entidades
            			 relacionadas de la entidad key
    	"""
		entDict={}
		entities = self.dom.getElementsByTagName("entities")
		for entity in entities:
			entDict[entity.getAttribute("entityName")]=self.getRelationshipsFromEntity(entity)
		return entDict

	def getEntityNameByPos(self, index):
		"""
        Método que devuelve el nombre de la entidad del modelo
        que ocupa una posición dada (index).

        @entities.33 -> Aqui se buscaría obtener el nombre de la entidad con pos 33.

    	"""
		return self.entNames[index]

	def getEntityNames(self):
		"""
        Método que devuelve la lista de nombres de entidades del modelo que se ha cargado.
    	"""
		return self.entNames

	def extractPosPojo(self, pojoString):
		"""
        Método que devuelve la posicion que ocupa un dto a partir de una cadena de texto.

        Para: "//@dtoModel/@dtos.33" se devuelve el entero 33
    	"""
		return int(re.findall("[0-9]+", pojoString)[0])

	def searchOrphanPojos(self):
		"""
        Método que devuelve una lista de warnings con 
        los POJOS que no se están devolviendo en ninguna query del modelo.
    	"""
		warnings=[]
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
			warnings.append(nameDtos[p]+' con posicion @dtos.'+str(p))
		return warnings

	def checkWrongTypesInPojos(self):
		"""
        Método que devuelve una lista de warnings con 
        atributos de los POJOS que pueden tener un tipo incorrecto.
    	"""
		warnings=[]
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
						warnings.append("Atributo "+name+" del POJO "+dto.getAttribute("dtoName")+" no es de tipo Long. Es de tipo "+type+" .¿Es correcto?")
				elif(self.searchWordInText("name",name) or self.searchWordInText("Name",name) or self.searchWordInText("Na",name)):
					if(not type==""):
						#añadir error
						warnings.append("Atributo "+name+" del POJO "+dto.getAttribute("dtoName")+" no es de tipo String.")
				elif(self.searchWordInText("descrip",name) or self.searchWordInText("Ds",name)):
					if(not type==""):
						#añadir error
						warnings.append("Atributo "+name+" del POJO "+dto.getAttribute("dtoName")+" no es de tipo String.")
				elif(self.searchWordInText("date",name) or self.searchWordInText("Date",name)):
					if(not(self.searchWordInText("Date",type))):
						#añadir error
						warnings.append("Atributo "+name+" del POJO "+dto.getAttribute("dtoName")+" no es de tipo Date.")
		return warnings

	def getDAOName(self):
		"""
        Método que devuelve el nombre del modelo cargado.
    	"""
		model=self.dom.getElementsByTagName("geniee:Model")
		return model[0].getAttribute("modelName")

	def getAttributesFromEntity(self,entity):
		"""
        Método que devuelve una lista conteniendo los nombres
        de los atributos de una entidad del modelo dada.
    	"""
		attrList=[]
		attributes=entity.getElementsByTagName("attributes")
		for at in attributes:
			attrList.append(at.getAttribute("attributeName"))
		return attrList

	def extractPosEntity(self, string):
		"""
        Método que devuelve la posicion de una entidad relacionada.

        A partir de la cadena //@entityModels.0/@entities.585" se obtiene el 585
    	"""
		return re.search('@entities.[0-9]+', string).group(0).split(".")[1]

	def getRelationshipsFromEntity(self,entity):
		"""
        Método que devuelve una lista con los nombres de las
        entidades que se relacionan con la entidad dada.
    	"""
		relList=[]
		rels=entity.getElementsByTagName("relationships")
		for r in rels:
			cadena=r.getAttribute("endRelationShip")
			pos=int(self.extractPosEntity(cadena))
			relList.append(self.getEntityNameByPos(pos))
		return relList

	def checkDuplicatedRepositories(self):
		"""
        Método que devuelve una lista de warnings con los nombres
        de los repositorios repetidos en el modelo, si los hay.
    	"""
		warnings=[]
		repoSet = set()
		repos = self.dom.getElementsByTagName("repositories")
		#cargar primer repo
		repoSet.add(repos[0].getAttribute("repositoryName"))
		self.checkDuplicatedQueriesInRepo(repos[0])
		for repo in repos[1:]:
			if repo.getAttribute("repositoryName") in repoSet:
				warnings.append('Repositorio repetido: '+repo.getAttribute("repositoryName"))
			else:
				self.checkDuplicatedQueriesInRepo(repo)
				repoSet.add(repo.getAttribute("repositoryName"))
		return warnings
		
	def checkDuplicatedQueriesInRepo(self,repo):
		"""
        Método que devuelve una lista de warnings con los nombres
        de las queries repetidas en un repositorio dado, si se da el caso.

        Tambien comprueba que no existan repositorios sin queries definidas.
    	"""
		warnings=[]
		qSet=set()
		queries=repo.getElementsByTagName("queries")
		#Comprobar que al menos tiene un metodo
		if len(queries) <1:
			warnings.append('El repositorio '+repo.getAttribute("repositoryName")+' no tiene queries definidas')
		else:
			#cargar primera query
			qSet.add(queries[0].getAttribute("queryName"))
			for q in queries[1:]:
				if q.getAttribute("queryName") in qSet:
					warnings.append('Metodo '+q.getAttribute("queryName")+' duplicado en repositorio '+repo.getAttribute("repositoryName"))
				else:
					qSet.add(q.getAttribute("queryName"))
		return warnings

	def checkRuleMethods(self):
		"""
        Método que analiza metodos de recuperacion de Reglas y devuelve una lista de warnings si:

        - no tiene como parametro de entrada un ruleEvent
        - no devuelve parametro de salida de tipo BigDecimal
    	"""
		warnings=[]
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
					warnings.append('Metodo de reglas '+q.getAttribute("queryName")+' no tiene parametro de entrada ruleEvent')
				retType=q.getElementsByTagName("return")
				if(retType[0].getAttribute("type").find("BigDecimal")==-1):
					warnings.append('Metodo de reglas '+q.getAttribute("queryName")+' no devuelve parámetro de tipo BigDecimal')
		return warnings

	def checkCatTextMethods(self):
		"""
        Método que analiza metodos de recuperacion de CatalogText y devuelve una lista de warnings si:

        - no recibe como parametros de entrada los 3 filtros (textType, textUse y publishMedia)
        - alguno de ellos no es de tipo Long
    	"""
		warnings=[]
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
							warnings.append('El parámetro '+param.getAttribute("parameterName")+' del metodo '+q.getAttribute("queryName")+' no es de tipo Long')
					elif(param.getAttribute("parameterName").lower().find("type")> -1):
						filters.add("type")
						#validarTipo
						if(param.getAttribute("type").find("Long")==-1):
							#error, filtro CatText no es Long
							warnings.append('El parámetro '+param.getAttribute("parameterName")+' del metodo '+q.getAttribute("queryName")+' no es de tipo Long')
					elif(param.getAttribute("parameterName").lower().find("media")> -1):
						filters.add("media")
						#validarTipo
						if(param.getAttribute("type").find("Long")==-1):
							#error, filtro CatText no es Long
							warnings.append('El parámetro '+param.getAttribute("parameterName")+' del metodo '+q.getAttribute("queryName")+' no es de tipo Long')
				if(len(filters)!=3):
					warnings.append('Falta al menos uno de los 3 filtros del CatalogText como parámetros de entrada en el metodo '+q.getAttribute("queryName"))
		return warnings

	def checkParametersType(self):
		"""
        Método que busca tipos incorrectos en parametros de entrada y devuelve una lista de warnings si:

        - algun parametro id no es de tipo Long
        - algun parametro queryDate no es de tipo Date
    	"""
		warnings=[]
		queries=self.dom.getElementsByTagName("queries")
		for q in queries:
			p=q.getElementsByTagName("parameters")
			for param in p:
				if(param.getAttribute("parameterName").find("id")> -1 or param.getAttribute("parameterName").find("Id")> -1):
					typ=param.getAttribute("type")
					if(typ.find("Long")==-1):
						if(typ==""):
							typ="String"
						warnings.append('Parametro '+param.getAttribute("parameterName")+' del metodo '+q.getAttribute("queryName")+ ' no es de tipo Long. Es de tipo '+typ+'.¿Es correcto?')
				elif(param.getAttribute("parameterName").find("queryDate")> -1 or param.getAttribute("parameterName").find("Date")> -1):
					typ=param.getAttribute("type")
					if(typ.find("Date")==-1):
						if(typ==""):
							typ="String"
						warnings.append('Parametro '+param.getAttribute("parameterName")+' del metodo '+q.getAttribute("queryName")+ ' no es de tipo Date. Es de tipo '+typ+'.¿Es correcto?')

		return warnings

	def checkDTDDocumentation(self):
		"""
        Método que devuelve una lista de warnings si:

        - alguna query no tiene relleno el campo Documentacion DTD
    	"""
		warnings=[]
		queries=self.dom.getElementsByTagName("queries")
		for q in queries:
			p=q.getAttribute("dtdDocumentation")
			if(p==""):
				warnings.append(q.getAttribute("queryName"))
		return warnings

	def findEntitiesAndFieldsInDTDDoc(self,dtdDoc):
		"""
        Método que recibe un texto Documentacion DTD y busca el patrón entidad.campo en filtros
        devolviendo una lista de los fragmentos que satisfagan el patrón.

        Nota: Se capitaliza la inicial de la entidad
    	"""
		entAndFields=re.findall("[a-zA-Z]{12,}"'\.'"[a-zA-Z]+", dtdDoc)
		out=[]
		for eF in entAndFields:
			capiteF=eF[0].upper()+eF[1:] #las entidades del modelo empiezan todos con mayuscula
			out.append(capiteF)
		return out

	def extractEntitiesFromJoins(self,dtdDoc):
		"""
        Método que recibe un texto Documentacion DTD y busca el patrón entidad1 JOIN entidad2 en filtros
        devolviendo una lista de los fragmentos que satisfagan el patrón.

        Ejemplo: devuelve ['ResppResourceSpec', 'INNER', 'JOIN', 'RespvResourceSpec']
    	"""
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
		"""
        Método que realiza algunas validaciones sobre las JOINS escritas. Devuelve una lista
        de warnings si:

        - si alguna entidad no tiene un nombre correcto o no existe en el modelo.
        - si se está haciendo una JOIN entre 2 entidades del modelo NO relacionadas.
    	"""
		warnings=[]
		queries=self.dom.getElementsByTagName("queries")
		for q in queries:
			dtdDoc=q.getAttribute("dtdDocumentation")
			joins=self.extractEntitiesFromJoins(dtdDoc)
			for j in joins: # entIzq INNER JOIN entDer o entIzq LEFT JOIN entDer o entIzq y entDer
				entIzq=j[0]
				entDer=j[-1]
				entIzqNew=entIzq[0].upper()+entIzq[1:]
				entDerNew=entDer[0].upper()+entDer[1:]
				if(entIzqNew not in self.attrEntModel):
					 warnings.append('Metodo: '+ q.getAttribute("queryName")+' #Entidad '+entIzqNew+' usada en la parte IZQUIERDA de una JOIN no existe o tiene un nombre distinto en el modelo.')
				if(entDerNew not in self.attrEntModel):
					 warnings.append('Metodo: '+ q.getAttribute("queryName")+' #Entidad '+entDerNew+' usada en la parte DERECHA de una JOIN no existe o tiene un nombre distinto en el modelo.')
				
				# verifica si es posible por modelo la JOIN entre entIzq y entDer
				# print(entDer)
				# si existe la entDerNew, miro si se puede hacer la JOIN
				if(entDerNew in self.relEntModel.keys()):
				 	if(entIzqNew not in self.relEntModel[entDerNew]):
				 		warnings.append('Metodo: '+ q.getAttribute("queryName")+' #No es posible por modelo hacer una JOIN entre '+entIzq+' y '+entDer+' .')
			return warnings

	def checkWrongEntities(self):
		"""
        Método que realiza algunas validaciones sobre los filtros de tipo entidad.campo. Devuelve una lista
        de warnings si:

        - si alguna entidad no tiene un nombre correcto o no existe en el modelo.
        - si un campo no es de la entidad.
    	"""
		warnings=set()
		queries=self.dom.getElementsByTagName("queries")
		for q in queries:
			dtdDoc=q.getAttribute("dtdDocumentation")
			entFields=self.findEntitiesAndFieldsInDTDDoc(dtdDoc)
			for filtro in entFields:
				entidad=filtro.split(".")[0]
				campo=filtro.split(".")[1]
				campo=campo[0].lower()+campo[1:] #los atributos en el modelo empiezan todos con minuscula
				#comprobar que la entidad existe
				if(entidad not in self.attrEntModel):
					 warnings.add('Metodo: '+ q.getAttribute("queryName")+' #Entidad '+entidad+' que se usa en los filtros no existe o tiene un nombre distinto en el modelo.')
				else: #entidad existe, comprobar que el campo es de esa entidad
					if(campo not in self.attrEntModel[entidad]):
						warnings.add('Metodo: '+q.getAttribute("queryName")+' #Campo '+campo+' de la entidad '+entidad+' que aparece como filtro no se encuentra como atributo de esa entidad en el modelo.')

			# 	# indexesINNER = [i for i,x in enumerate(l) if x == "INNER"]
			# 	# for ind in indexesINNER:
			# 		# if(len(l[ind-1])>5):
			# 			# print(l[ind-1])
			# 	# indexesJOIN = [i for i,x in enumerate(l) if x == "JOIN"]
			# 	# for ind in indexesJOIN:
			# 		# if(len(l[ind+1])>5):
			# 			# print(l[ind+1])
		return sorted(warnings)

	def searchWordInText(self,word, text):
		"""
        Método que busca una cadena en un texto y 
        devuelve True si existe y False en caso contrario.
    	"""
		results=re.findall(word, text)
		if(results==[]):
			return False
		return True

	def checkKeywordsInDoc(self):
		"""
        Método que realiza algunas validaciones entre los parametros y la documentacion de la consulta. Devuelve una lista
        de warnings si:

        - si se hace referencia a un queryDate que NO aparece como parametro de entrada.
        - si aparece la palabra "lista" y NO se devuelve una Colecction
    	"""
		warnings=[]
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
					warnings.append('En la DOC del metodo '+q.getAttribute("queryName")+' se hace referencia a un queryDate que no aparece como parámetro de entrada')
			#Comprobar lista en DOC y que devuelva Colecction or Collection
			if(listaKW):
				retType=q.getElementsByTagName("return")
				if(not self.searchWordInText("Colecction",retType[0].getAttribute("xsi:type")) and not self.searchWordInText("Collection",retType[0].getAttribute("xsi:type"))):
					warnings.append('En la DOC del metodo '+q.getAttribute("queryName")+' aparece "lista" y el metodo no devuelve una lista de elementos')
		return warnings

	def generateReport(self):
		"""
		Método que invoca a las funciones de validación, captura los warnings y los vuelca en un informe txt.
		"""
		name=self.getDAOName()
		f = open('Informe_'+name+'.txt', 'w')
		f.write('**********************************************************'+'\n')
		f.write('Validaciones del DAO '+self.getDAOName()+'\n')
		f.write('**********************************************************'+'\n\n')
		f.write("Chequeando repositorios y metodos duplicados..."+'\n')
		f.write("==============================================="+'\n')
		w=self.checkDuplicatedRepositories()
		if(w==[]):
			f.write("OK"+'\n')
		else:
			for warning in w:
				f.write(warning+'\n')
		f.write('\n\n'+"Chequeando parametros en metodos de reglas..."+'\n')
		f.write("============================================="+'\n')
		w=self.checkRuleMethods()
		if(w==[]):
			f.write("OK"+'\n')
		else:
			for warning in w:
				f.write(warning+'\n')
		f.write('\n\n'+"Chequeando tipos de parametros..."+'\n')
		f.write("================================="+'\n')
		w=self.checkParametersType()
		if(w==[]):
			f.write("OK"+'\n')
		else:
			for warning in w:
				f.write(warning+'\n')
		f.write('\n\n'+"Chequeando metodos sin Documentacion..."+'\n')
		f.write("======================================="+'\n')
		w=self.checkDTDDocumentation()
		if(w==[]):
			f.write("OK"+'\n')
		else:
			for warning in w:
				f.write(warning+'\n')
		f.write('\n\n'+"Chequeando entidad.campo en las consultas..."+'\n')
		f.write("======================================="+'\n')
		w=self.checkWrongEntities()
		if(len(w)==0):
			f.write("OK"+'\n')
		else:
			for warning in w:
				f.write(warning+'\n')
		f.write('\n\n'+"Chequeando metodos CatalogText..."+'\n')
		f.write("======================================="+'\n')
		w=self.checkCatTextMethods()
		if(w==[]):
			f.write("OK"+'\n')
		else:
			for warning in w:
				f.write(warning+'\n')
		f.write('\n\n'+"Chequeando filtros en la DOC que no aparecen como parámetros de entrada..."+'\n')
		f.write("======================================="+'\n')
		w=self.checkKeywordsInDoc()
		if(w==[]):
			f.write("OK"+'\n')
		else:
			for warning in w:
				f.write(warning+'\n')
		f.write('\n\n'+"POJOS no devueltos en ningun metodo:"+'\n')
		f.write("======================================="+'\n')
		w=self.searchOrphanPojos()
		if(w==[]):
			f.write("OK"+'\n')
		else:
			for warning in w:
				f.write(warning+'\n')
		f.write('\n\n'+"Comprobando tipos en atributos de los POJOS..."+'\n')
		f.write("======================================="+'\n')
		w=self.checkWrongTypesInPojos()
		if(w==[]):
			f.write("OK"+'\n')
		else:
			for warning in w:
				f.write(warning+'\n')
		f.write('\n\n'+"Comprobando validez de las JOINS..."+'\n')
		f.write("======================================="+'\n')
		w=self.checkValidityEntitiesJoins()
		if(w==[]):
			f.write("OK"+'\n')
		else:
			for warning in w:
				f.write(warning+'\n')
		print("XMI validado. Consulta el informe generado.")
		f.close()


if(len(sys.argv)<2):
	raise ValueError('Se debe introducir al menos un fichero XMI para validar.')
else:
	for doc in sys.argv[1:]:
		if not doc.endswith('.xmi'):
			raise ValueError('El parámetro no es un fichero XMI')
		a=XMIValidator(doc).generateReport()