# -*- coding: utf-8 -*-
'''Basic programmer for 16-bit PIC microcontrollers

@author     Javier Casas (javcasas AT gmail net)
@version    1.0
'''
__author__ = "Javier Casas (javcasas AT gmail net)"
__version__ = "1.0"


import time
import ChipIdentifier

def getBit(cad,n):
	"""Returns the n-th bit of cad"""
	# lee el bit n de cad
	mascara = 1 << n
	b=cad & mascara
	if (b == mascara):
		return 1
	else:
		return 0

def setBit(cad, n, val):
	"""Returns cad with the n-th bit set to val"""
	#establece el bit n de cad a val
	if val == 0:
		return cad
	mascara = 1 << n
	cad = cad | mascara
	return cad

def listaBits(principio, fin):
	"""Returns a list in the form [principio, ..., fin], made of consecutive integers"""	
	if fin < principio:
		return range(principio, fin - 1, -1)
	else:
		return range(principio, fin + 1)


class CommandProgrammer:
	"""Basic ICSP controller for 16-bit PICs"""

	def setBigBangProgrammer(self, bb):
		self.bb = bb

	
	ICSPmagicCode=0x4D434851
	EICSPmagicCode=0x4D434850


	def enterICSP(self):
		"""Puts the MCU in ICSP mode, ready to accept instructions."""	
		self.bb.begin()
		
		self.bb.set_vdd(1)
		self.bb.commit()

		self.bb.set_pgd(0)
		self.bb.set_pgc(0)
		self.bb.commit()
		self.bb.set_mclr(0)
		self.bb.commit()
		self.bb.set_mclr(1)
		self.bb.commit()
		self.bb.set_mclr(0)
		self.bb.commit()
		for i in listaBits(31,0):
			bit=getBit(self.ICSPmagicCode, i)
			self.bb.set_pgd(bit)
			self.bb.commit()
			self.bb.set_pgc(1)
			self.bb.commit()
			self.bb.set_pgc(0)
			self.bb.commit()

		self.bb.set_pgd(0)
		self.bb.commit()
		time.sleep(0.005)
		self.bb.set_mclr(1)
		time.sleep(0.03)

	def leaveICSP(self):
		"""Stops the ICSP mode."""	
		self.bb.set_mclr(0)
		self.bb.commit()
		self.bb.set_vdd(0)
		self.bb.commit()
		self.bb.end()
		

	def SIX(self, comando, primera_ejecucion=False):
		"""SIX, sends a command to the MCU
		Parameters:
		comando -- the command in 24-bit format
		primera_ejecucion -- If True, adds 5 extra clocks for the first instruction, as indicated in the datasheet.
		"""
		self.bb.set_pgd(0)
		self.bb.commit()

		for i in listaBits(1,4): #4 ceros
			self.bb.set_pgc(1)
			self.bb.commit()
			self.bb.set_pgc(0)
			self.bb.commit()

		if primera_ejecucion: #5 ceros extra
			for i in listaBits(1,5): 
				self.bb.set_pgc(1)
				self.bb.commit()
				self.bb.set_pgc(0)
				self.bb.commit()

		for i in listaBits(0,23):
			bit=getBit(comando, i)
			self.bb.set_pgd(bit)
			self.bb.commit()
			self.bb.set_pgc(1)
			self.bb.commit()
			self.bb.set_pgc(0)
			self.bb.commit()

	def REGOUT(self):
		"""REGOUT, extracts VISI register from the MCU"""
		res=0
		self.bb.set_pgd(1)
		self.bb.commit()
		self.bb.set_pgc(1)
		self.bb.commit()
		self.bb.set_pgc(0)
		self.bb.commit()

		self.bb.set_pgd(0)
		self.bb.commit()

		for i in listaBits(1,11):
			self.bb.set_pgc(1)
			self.bb.commit()
			self.bb.set_pgc(0)
			self.bb.commit()

		for i in listaBits(0,15):
			self.bb.set_pgc(1)
			self.bb.commit()

			res = setBit(res, i, self.bb.read_pgd())

			self.bb.set_pgc(0)
			self.bb.commit()

		return res

	def startPic(self):
		"""Applies VDD and sets MCLR to 1"""
		self.bb.begin()
		
		self.bb.set_vdd(1)
		self.bb.commit()
		self.bb.set_mclr(1)
		self.bb.commit()

	def stopPic(self):
		"""Removes VDD and sets MCLR to 0"""
		
		self.bb.set_mclr(0)
		self.bb.commit()
		self.bb.set_vdd(0)
		self.bb.commit()

		self.bb.end()




class Programmer:
	"""Implements basic commands for reading and programming a MCU"""

	def setCommandProgrammer(self, c):
		self.c = c

	def begin(self):
		"""Begins a transaction"""
		self.c.enterICSP()
		self.c.SIX(0, True)
	
	def end(self):
		"""Ends a transaction"""
		self.c.leaveICSP()

	def startPic(self):
		self.c.startPic()

	def stopPic(self):
		self.c.stopPic()

	def resetPic(self):
		self.stopPic()
		self.startPic()

	def readMem(self, address, nitems=64):
		"""Reads address of the program memory of the microcontroller.
		It must be run as a transaction (inside begin-end calls)
		Parameters:
		address -- The address to read from
		nitems -- the number of items read
		    Must be multiple of 4 and up to 64
		Returns a list of the values read
		"""
		#Dirección de 24 bits
		#value 64 enteros de 24 bits
		#nitems es la cantidad de direcciones a leer, debe ser múltiplo de 4, max 64

		if (nitems % 4) != 0:
			print "error en Programmer.readMem()"
			return False
		value = []

		self.c.SIX(0x040200)
		self.c.SIX(0x040200)
		self.c.SIX(0x000000)

		msb=(address & 0xff0000) >> 16
		self.c.SIX(0x200000 | (msb << 4))
		self.c.SIX(0x880190)
		lsb=(address & 0xffff)
		self.c.SIX(0x200006 | (lsb << 4))

		indice = 0
		for indice in range(0, nitems, 4):
			res = [1,1,1,1,1,1]
			self.c.SIX(0xeb0380)
			self.c.SIX(0x000000)

			self.c.SIX(0xba1b96)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)

			self.c.SIX(0xbadbb6)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)

			self.c.SIX(0xbadbd6)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)

			self.c.SIX(0xba1bb6)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)

			self.c.SIX(0xba1b96)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)

			self.c.SIX(0xbadbb6)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)

			self.c.SIX(0xbadbd6)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)

			self.c.SIX(0xba1bb6)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)

			self.c.SIX(0xa883c20)
			self.c.SIX(0x000000)
			res[0] = self.c.REGOUT()
			self.c.SIX(0x000000)

			self.c.SIX(0xa883c21)
			self.c.SIX(0x000000)
			res[1] = self.c.REGOUT()
			self.c.SIX(0x000000)

			self.c.SIX(0xa883c22)
			self.c.SIX(0x000000)
			res[2] = self.c.REGOUT()
			self.c.SIX(0x000000)

			self.c.SIX(0xa883c23)
			self.c.SIX(0x000000)
			res[3] = self.c.REGOUT()
			self.c.SIX(0x000000)

			self.c.SIX(0xa883c24)
			self.c.SIX(0x000000)
			res[4] = self.c.REGOUT()
			self.c.SIX(0x000000)

			self.c.SIX(0xa883c25)
			self.c.SIX(0x000000)
			res[5] = self.c.REGOUT()
			self.c.SIX(0x000000)

			res2=self.unpackInstructionWords(res)
			for i in res2:
				value.append(i)


		self.c.SIX(0x040200)
		self.c.SIX(0x000000)

		return value



	def writeMem(self, address, value):
		"""Writes the program memory at the address specified.
		It must be run as a transaction (inside begin-end calls)
		Parameters:
		address -- The address to write into from
		value -- The values to write
		    Must be an iterable of 64 items (0..63)
		    Each item is a full instruction word (24 bits)
		"""

		#Dirección de 24 bits
		#value 64 enteros de 24 bits

		indice = 0
		self.c.SIX(0x040200)
		self.c.SIX(0x040200)
		self.c.SIX(0x24001a)
		self.c.SIX(0x883b0a)

		msb=(address & 0xff0000) >> 16
		self.c.SIX(0x200000 | (msb << 4))
		self.c.SIX(0x880190)
		lsb=(address & 0xffff)
		self.c.SIX(0x200007 | (lsb << 4))

		for indice in range(0, 64, 4):
			dat=value[indice:indice + 4]
			datos = self.packInstructionWords(dat)
			self.c.SIX(0x200000 | (datos[0] << 4))
			self.c.SIX(0x200001 | (datos[1] << 4))
			self.c.SIX(0x200002 | (datos[2] << 4))
			self.c.SIX(0x200003 | (datos[3] << 4))
			self.c.SIX(0x200004 | (datos[4] << 4))
			self.c.SIX(0x200005 | (datos[5] << 4))

			self.c.SIX(0xeb0300)
			self.c.SIX(0x000000)
			self.c.SIX(0xbb0bb6)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)
			self.c.SIX(0xbbdbb6)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)
			self.c.SIX(0xbbebb6)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)
			self.c.SIX(0xbb1bb6)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)
			self.c.SIX(0xbb0bb6)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)
			self.c.SIX(0xbbdbb6)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)
			self.c.SIX(0xbbebb6)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)
			self.c.SIX(0xbb1bb6)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)

		self.c.SIX(0xa8e761)
		self.c.SIX(0x000000)
		self.c.SIX(0x000000)
		self.c.SIX(0x000000)
		self.c.SIX(0x000000)

		time.sleep(0.002) #P13: 1.28 ms

		continuar = True
		reintentos = 0
		while(continuar):
			self.c.SIX(0x803b00)
			self.c.SIX(0x883c20)
			self.c.SIX(0x000000)
			res = self.c.REGOUT()
			self.c.SIX(0x040200)
			self.c.SIX(0x000000)

			continuar = (res & 0x8000) == 0
			reintentos += 1
			if reintentos > 20:
				print "Timeout en writeMem"
				continuar = False

		#self.c.leaveICSP()
		return

	def readConfigMem(self):
		"""Reads all the configuration registers.
		It must be run as a transaction (inside begin-end calls)
		"""
		#Lee toda la memoria de configuración
		return self.readMem(0xf80000,12)

	def writeConfigMem(self, datos):
		"""Writes all the configuration registers.
		It must be run as a transaction (inside begin-end calls)
		Parameters:
		datos -- the configuration registers in an iterable form of 12 items
		"""
		#escribe toda la memoria de configuracion

		self.c.SIX(0x040200)
		self.c.SIX(0x040200)
		self.c.SIX(0x000000)

		self.c.SIX(0x200007)

		self.c.SIX(0x24000a)
		self.c.SIX(0x883b0a)

		self.c.SIX(0x200f80)
		self.c.SIX(0x880190)

		for i in listaBits(0,11):
			dat=datos[i] & 0xffff
			self.c.SIX(0x200000 | (dat << 4))
	
			self.c.SIX(0xbb1b80)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)
	
			self.c.SIX(0xa8e761)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)
			self.c.SIX(0x000000)

			time.sleep(0.025) #P20

			continuar = True
			reintentos = 0
			while(continuar):
				self.c.SIX(0x803b00)
				self.c.SIX(0x883c20)
				self.c.SIX(0x000000)
				reg = self.c.REGOUT()
				self.c.SIX(0x040200)
				self.c.SIX(0x000000)
				continuar = (reg & 0x8000) == 0
				reintentos += 1
				if reintentos > 20:
					print "Timeout en writeMem"
					continuar = False





	def eraseChip(self):
		"""Erases the microcontroller memory.
		It must be run as a transaction (inside begin-end calls)
		"""
		#Borra el chip
		self.c.SIX(0x040200)
		self.c.SIX(0x040200)
		self.c.SIX(0x000000)
		self.c.SIX(0x2404fa)
		self.c.SIX(0x883b0a)
		self.c.SIX(0xa8e761)
		self.c.SIX(0x000000)
		self.c.SIX(0x000000)
		self.c.SIX(0x000000)
		self.c.SIX(0x000000)

		#esperamos P11 (330 ms)
		time.sleep(0.33)

	def readDevId(self):
		"""Reads the device identifier and device revision.
		It must be run as a transaction (inside begin-end calls)
		Returns a list of 2 items: [devId, revId]
		"""
		#Lee la descripción del chip
		dat=self.readMem(0xff0000, 4)
		return dat[0:2]

	def packInstructionWords(self, datos):
		"""Packs 4 24-bits instructions into 6 16-bits integers as specified in the datasheet.
		Returns a list of 6 items
		"""
		#datos es un array de 4 ints, de los cuales se interpretan los 24 bits de menor valor
		#Devuelve un array de 6 ints, de los cuales son válidos los 16 bits de menor valor
		res=[1,1,1,1,1,1]

		res[0]=datos[0] & 0xffff
		res[1]=(((datos[1] & 0xff0000) >> 8) | ((datos[0] & 0xff0000) >> 16)) & 0xffff
		res[2]=datos[1] & 0xffff
		res[3]=datos[2] & 0xffff
		res[4]=(((datos[3] & 0xff0000) >> 8) | ((datos[2] & 0xff0000) >> 16)) & 0xffff
		res[5]=datos[3] & 0xffff

		return res

	def unpackInstructionWords(self, datos):
		"""Unpacks 6 16-bits packed instructions into 4 24-bits integers as specified in the datasheet.
		Returns a list of 4 items
		"""
		#datos es un array de 6 ints, de los cuales son válidos los 16 bits de menor valor		
		#devuelve un array de 4 ints, de los cuales se interpretan los 24 bits de menor valor
		res=[1,1,1,1]

		res[0] = datos[0]
		msb = (datos[1] & 0xff) << 16
		res[0] = res[0] | msb

		res[1] = datos[2]
		msb = (datos[1] & 0xff00) << 8
		res[1] |= msb

		res[2] = datos[3]
		msb = (datos[4] & 0xff) << 16
		res[2] |= msb		

		res[3] = datos[5]
		msb = (datos[4] & 0xff00) << 8
		res[3] |= msb

		return res




bbp=CommandProgrammer()


def test():
	bbp.enterICSP()

	bbp.SIX(0, True)
	bbp.SIX(0x040200)
	bbp.SIX(0x040200)
	bbp.SIX(0x000000)

	bbp.SIX(0xEC2784)
	bbp.SIX(0xEC2784)
	bbp.SIX(0x000000)
	bbp.SIX(0x000000)
	dat = bbp.REGOUT()
	if dat != 2:
		print "error en test 1.1: ", hex(dat)
	bbp.SIX(0xEC2784)
	bbp.SIX(0xEC2784)
	bbp.SIX(0x000000)
	dat = bbp.REGOUT()
	if dat != 4:
		print "error en test 1.2: ", hex(dat)

	bbp.leaveICSP()

def test2():
	p=Programmer()
	cads = []
	cads.append(0x123456)
	cads.append(0x789abc)
	cads.append(0xdef123)
	cads.append(0x456789)
	res=p.packInstructionWords(cads)
	res2=p.unpackInstructionWords(res)
	if cads != res2:
		print "error en test 2:"
		for i in cads:
			print hex(i),
		print ""
		for i in res:
			print hex(i),
		print ""
		for i in res2:
			print hex(i),
		print ""

def test3():
	p=Programmer()
	datos=[]
	p.begin()
	for i in listaBits(0,63):
		datos.append(i)
	p.writeMem(0x0000, datos)
	datos2=p.readMem(0x0000)
	p.end()
	if datos != datos2:
		print "error en test 3:"
		for i in datos:
			print i,
		print ""
		for i in datos2:
			print i,
		print ""

def test4():
	p=Programmer()
	datos=[]
	p.begin()
	p.eraseChip()
	datos=p.readMem(0x0000)
	p.end()
	for dato in datos:
		if dato != 0xffffff:
			print "error de borrado:", hex(dato)
			break

def test5():
	p=Programmer()
	datos = p.readConfigMem()
	for dato in datos:
		print hex(dato)
	datos2 = p.readMem(0xf80000,12)
	for dato in datos2:
		print hex(dato)
	
	i=0
	for i in range(0,12):
		print hex(datos[i]), hex(datos2[i])

def test6():
	p=Programmer()
	print hex(p.readDevId()[0]),hex(p.readDevId()[1])
	michip=ChipIdentifier.ChipIdentifier()
	michip.setDevId(p.readDevId())
	print michip.fullDesc()



def main():


#	test()
#	test2()
	test3()
#	test4()
#	test5()
#	test6()

if __name__ == "__main__":
	main()
