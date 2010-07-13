# -*- coding: utf-8 -*-
'''Command-line utility for reading, erasing and programming a 16-bit PIC microcontroller

@author     Javier Casas (javcasas AT gmail net)
@version    1.0
'''
__author__ = "Javier Casas (javcasas AT gmail net)"
__version__ = "1.0"


import BitBang
import CommandProgrammer
import ChipIdentifier

import getopt, sys

import intelhex
import sys




class extractor24bits:
	"""
	Getter and setter for reading a intel hex file containing a 16-bit PIC microcontroller program
	"""

	def __init__(self, hex):
		"""Makes an instance for the specified hex object
		Parameters:
		hex --  a intelhex.IntelHex() object"""
		self.mihex=hex

	def extrae_direcciones(self):
		""" Returns the addresses used in the hex object"""
		dirs = self.mihex.addresses()
		res=[]
		for dir in dirs:
			if (dir & 0x3) == 3:
				res.append(dir >> 2)
		return res

	def make_slices(self):
		""" Returns the addresses used in the hex object as a list of pairs (begin, end)"""
		dirs = self.extrae_direcciones()
		res = []
		inicial =0
		final = 0
		anterior = -1
		for dir in dirs:
			if dir == anterior + 1:
				final = dir
			else:
				res.append((inicial, final))
				inicial = final = dir

			anterior = dir

		res.append((inicial, final))

		if res[0] == (0,0):
			res.remove((0,0))

		return res

	def __getitem__(self, addr):
		if isinstance(addr, slice):
			res = []
			primero = addr.start or 0
			ultimo = addr.stop or 0
			incremento = addr.step or 1
			for i in range(primero, ultimo, incremento):
				res.append(self[i])
			return res
		dir = addr << 2
		val = self.mihex[dir + 0]
		val |= self.mihex[dir + 1] << 8
		val |= self.mihex[dir + 2] << 16
		val |= self.mihex[dir + 3] << 24
		return val

	def __setitem__(self, addr, bits):
		dir = addr << 2
		self.mihex[dir + 0]= bits & 0xff
		self.mihex[dir + 1]= (bits & 0xff00) >> 8
		self.mihex[dir + 2]= (bits & 0xff0000) >> 16
		self.mihex[dir + 3] = 0x00

class fixRegisters:
	"""
	Fixes invalid values in the configuration registers
	"""

	def fixPIC24HJ12GP201(self, extractor):
		extractor[0xF80002]=0xF


	def fix(self, id, extractor):
		if id in ["PIC24HJ12GP201","PIC24HJ12GP202"]:
			self.fixPIC24HJ12GP201(extractor)


def createProgrammer(name):
	""" Returns a CommandProgrammer.Programmer object using the specified hardware.
	Supported hardware:
	"CheapParport" -- Basic programmer using parallel port
	
	"""
	if name == "CheapParport":
		bb = BitBang.BitBangCheapParport() 
		cp = CommandProgrammer.CommandProgrammer()
		cp.setBigBangProgrammer(bb)

		res = CommandProgrammer.Programmer()
		res.setCommandProgrammer(cp)

		return res
	else:
		return Null


def identificar(programador):
	""" Identifies the chip using the specified programmer.
	Returns a pair of items: (devid, fulldesc):
	-- devid: list of 2 items: [chip device id, chip revision id]
	-- fulldesc: human-readable string with the description of the chip	
	"""
	programador.begin()
	devid=programador.readDevId()
	programador.end()
	chip=ChipIdentifier.ChipIdentifier()
	chip.setDevId(devid)
	return (devid,chip.fullDesc())

def progresoLectura(region, porcentaje):
	""" Basic callback for "leer" function.
	Prints a string showing the progress.
	"""	
	print "Leyendo "+region + ": " + str(int(porcentaje)) + "% completo"


def leer(programador, callback=progresoLectura):
	""" Reads the memory of a MCU using the specified programmer and calling the specified function for showing progress.
	Parameters:
	programador -- the programmer
	callback -- a function for showing the progress of the reading
	Returns 3 items (data, executive, regs):
	-- data: the program memory
	-- executive: the programming executive
	-- regs: the configuration registers
	"""	
	programador.begin()
	devid=programador.readDevId()
	chip=ChipIdentifier.ChipIdentifier()
	chip.setDevId(devid)
	flash = chip.flash
	#Leemos el flash
	data_ret=[]

	
	callback("FLASH", 0)
	for i in range(0, flash, 64):
		res=programador.readMem(i << 1)
		data_ret.extend(res)

		porcentaje = float(i) / float(flash) * 100
		porcentaje = porcentaje * 0.5
		callback("FLASH", porcentaje)


	#leemos el programming executive
	prog_executive=[]
	len_pe=chip.programmingExecutive
	callback("Programming Executive", 50)
	for i in range(0, len_pe, 64):
		res=programador.readMem((i << 1) + 0x800000)
		prog_executive.extend(res)

		porcentaje = float(i) / float(len_pe) * 100.0
		porcentaje = porcentaje * 0.45 + 50
		callback("Programming Executive", porcentaje)
		
		#print "Leyendo programming executive: " + str(i) + " de " + str(len_pe)

	programador.end()
	programador.begin()
	callback("Configuration", 95)
	regs=programador.readConfigMem()
	#callback("Configuration", 100)
	programador.end()

	return data_ret, prog_executive, regs

def progresoEscritura(region, porcentaje):
	""" Basic callback for "escribir" function.
	Prints a string showing the progress.
	"""	
	print "Escribiendo " + region + ": " + str(int(porcentaje)) + "% completo"


def escribir(programador, extractor, callback=progresoEscritura):
	""" Writes the memory of a MCU using the specified programmer and calling the specified function for showing progress.
	Parameters:
	programador -- the programmer
	extractor -- an instance of extractor24bits containing the program
	callback -- a function for showing the progress of the writing
	"""	
	#escribe los datos del extractor24bits en el programador especificado

	programador.begin()
	devid=programador.readDevId()
	programador.end()
	chip=ChipIdentifier.ChipIdentifier()
	chip.setDevId(devid)
	print chip.fullDesc()

	max_addr_flash = chip.flash
	max_addr_pe = chip.programmingExecutive

	def vacio(area):
		for i in area:
			if i != 0xffffffff:
				return False
		return True

	#escribir flash
	callback("FLASH", 0)
	programador.begin()
	memoria1 = extractor[0:0+64]
	
	for i in range(0, max_addr_flash, 64):
		memoria = extractor[i:i+64]
		if not vacio(memoria):
			programador.writeMem(i << 1, memoria)

			porcentaje = float(i) / float(max_addr_flash) * 100.0
			porcentaje = porcentaje * 0.5
			callback("FLASH", porcentaje)


	#escribir programming executive
	callback("Programming Executive", 50)
	for i in range(0x800000, 0x800000 + max_addr_pe, 64):
		memoria = extractor[i:i+64]
		if not vacio(memoria):
			programador.writeMem(i << 1, memoria)

			porcentaje = float(i - 0x800000) / float(max_addr_pe - 0x800000) * 100.0
			porcentaje = porcentaje * 0.45 + 50
			callback("Programming Executive", porcentaje)


	#escribir registros de configuracion
	fix=fixRegisters()
	fix.fix(chip.descId, extractor)
	callback("Configuration", 95)
	dir = 0xf80000 >> 1
	memoria = extractor[dir:dir + 12]
	print hex(dir)
	print "Rangos"
	for (i,j) in extractor.make_slices():
		print hex(i), hex(j)
	print "Registros"
	for i in memoria:
		print hex(i)
	programador.writeConfigMem(memoria)
	programador.end()

def borrar(programador):
	""" Writes the MCU using the specified programmer.
	programador -- the programmer
	"""	
	#Borra el microcontrolador
	programador.begin()
	programador.eraseChip()
	programador.end()




def usage():
	print """
pic24programmer: PIC24, dsPIC30 & dsPIC33 programmer
Usage:
	pic24programmer [options] command

Available commands:
	identify: Identifies the chip
	read: reads the chip
	write: programs the chip
	erase: erases the chip
	h, -h, help, --help: shows this help

Available options:
	--write-file=<file>: Saves the read memory to the specified file in intel hex format.
	--read-file=<file>: Reads the program memory from the specified file in intel hex format.
	--programmer=<programmer>: Uses the specified programmer

Available programmers:
	CheapParport: basic parallel port programmer

"""

def main():
	"""Main function"""
	try:
		opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "write-file=", "read-file=", "programmer="])
	except getopt.GetoptError, err:
		# print help information and exit:
		print str(err) # will print something like "option -a not recognized"
		usage()
		sys.exit(2)
	output = None
	verbose = False
	if len(args) != 1:
		usage()
		sys.exit(2)
	else:
		comando=args[0]


	programador=""
	write_file=""
	read_file=""

	for o, a in opts:
		if o == "-v":
			verbose = True
		elif o in ("-h", "--help"):
			usage()
			sys.exit()
		elif o == ("--write-file"):
			write_file = a
		elif o == ("--read-file"):
			read_file = a
		elif o == ("--programmer"):
			programador=a
		else:
			usage()
			print "Error: unknown option: " + o
			sys.exit(2)


	if programador=="":
		usage()
		print "Error: No programmer specified"
		sys.exit(2)
	elif programador == ("CheapParport"):
		prg = createProgrammer(programador)
	else:
		usage()
		print "Error: unknown programmer: " + programador
		sys.exit(2)

	if comando == ("identify"):
		devid, info=identificar(prg)
		for i in devid:
			print hex(i),
		print ""
		print info

	elif comando == ("read"):
		print "Reading..."
		memoria_usuario, programming_executive, registros_configuracion = leer(prg)

		contenido=intelhex.IntelHex()
		extractor=extractor24bits(contenido)
		dir = 0
		for i in memoria_usuario:
			if i != 0xffffff:
				extractor[dir] = i
			dir = dir + 1

		print dir

		if write_file == "":
			print "FLASH:"
			print contenido.dump()

			dir = 0
			p_e = intelhex.IntelHex()
			extractor2=extractor24bits(p_e)
			for i in programming_executive:
				if i != 0xffffff:
					extractor2[dir + (0x800000 >> 1)] = i
				dir = dir + 1

			print "Programming executive:"
			print p_e.dump()

			print "Configuration registers:"
			for i in range(0, 3):
				for j in range(0,4):
					print hex( registros_configuracion[i+j] ),
				print ""
		else:
			dir = 0
			for i in programming_executive:
				if i != 0xffffff:
					extractor[dir + (0x800000 >> 1)] = i
				dir = dir + 1

			dir = 0
			for i in registros_configuracion:
				extractor[(0xf80000 >> 1) + dir] = i
				dir = dir + 1
			contenido.tofile(write_file, "hex")
	elif comando == ("write"):
		if read_file == "":
			usage()
			print "Error: read file not specified (--read-file parameter)"
			sys.exit(2)
		else:
			contenido=intelhex.IntelHex()
			contenido.loadfile(read_file, "hex")
			extractor=extractor24bits(contenido)
			escribir(prg, extractor)
			#for i in range(0,0x84, 4):
			#	print hex(i), hex(extractor[i]), hex(extractor[i+1]), hex(extractor[i+2]), hex(extractor[i+3])

	elif comando == ("erase"):
		print "Erasing..."
		borrar(prg)

	elif comando in ("h","help"):
		usage()
		sys.exit()
	else:
		usage()
		print "Error: unknown command: " + comando
		sys.exit(2)

	prg.startPic()


if __name__ == "__main__":
	#main_test()
	main()

