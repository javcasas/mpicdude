# -*- coding: utf-8 -*-

'''Identifying functions for 16-bit PIC microcontrollers

@author     Javier Casas (javcasas AT gmail net)
@version    1.0
'''
__author__ = "Javier Casas (javcasas AT gmail net)"
__version__ = "1.0"


_1k = 1024
_2k = 1024 * 2
_4k = 1024 * 4
_6k = 1024 * 6

ids={
	#id : (nombrechip, tabla de revisiones, tamaño flash(direcciones), tamaño ram(bytes), tamaño programming executive(kdirecciones)
	0x0C00 : ("dsPIC33FJ06GS101", "dsPIC33FJ06GS101", _2k, 256, 1),
	0x0C01 : ("dsPIC33FJ06GS102", "dsPIC33FJ06GS101", _2k, 256, 1),
	0x0C02 : ("dsPIC33FJ06GS202", "dsPIC33FJ06GS101", _2k, _1k, 1),
	0x0C04 : ("dsPIC33FJ16GS402", "dsPIC33FJ06GS101", _6k, _2k, 1),
	0x0C06 : ("dsPIC33FJ16GS404", "dsPIC33FJ06GS101", _6k, _2k, 1),
	0x0C03 : ("dsPIC33FJ16GS502", "dsPIC33FJ06GS101", _6k, _2k, 1),
	0x0C05 : ("dsPIC33FJ16GS504", "dsPIC33FJ06GS101", _6k, _2k, 1),

	0x0802 : ("dsPIC33FJ12GP201", "dsPIC33FJ12GP201", _4k, _1k, _1k),
	0x0803 : ("dsPIC33FJ12GP202", "dsPIC33FJ12GP201", _4k, _1k, _1k),
	0x0800 : ("dsPIC33FJ12MC201", "dsPIC33FJ12GP201", _4k, _1k, _1k),
	0x0801 : ("dsPIC33FJ12MC202", "dsPIC33FJ12GP201", _4k, _1k, _1k),

	0x080A : ("PIC24HJ12GP201", "PIC24HJ12GP20x", _4k, _1k, _1k),
	0x080B : ("PIC24HJ12GP202", "PIC24HJ12GP20x", _4k, _1k, _1k)
	}


revtables={
		"dsPIC33FJ06GS101":
		{
			0x3000 : "A0 Revision",
			0x3001 : "A1 Revision",
			0x3002 : "A2 Revision"
		},

		
		"dsPIC33FJ12GP201":
		{
			0x3001 : "A2 Revision",
			0x3002 : "A3 Revision",
			0x3003 : "A4 Revision"
		},

		"PIC24HJ12GP20x":
		{
			0x3001 : "A2 Revision",
			0x3002 : "A3 Revision",
			0x3003 : "A4 Revision",
			0x3005 : "A5 Revision"
		}
	}



class ChipIdentifier():
	"""Identifies 16 bit PIC microcontrollers based on chip id and revision number"""

	id = 0
	rev = 0
	descId="Unknown chip"
	descRev="Unknown revision"
	flash=0
	ram=0
	programmingExecutive=0

	def setDevId(self, devid):
		"""Identifies a PIC microcontroller, setting internal vars
		Params:
		devid[0] -- device identifier
		devid[1] -- chip revision
		Sets:
		id -- device identifier
		rev -- chip revision
		descId -- chip name
		descRev -- chip revision description
		flash -- chip flash memory size in addresses
		ram -- chip ram memory size in bytes
		programmingExecutive -- chip PE size in addresses
		"""
		#dev id array de 2 enteros
		def revtable(tabla, revid):
			if tabla in revtables:
				if revid in revtables[tabla]:
					return revtables[tabla, id]

			return ("Unknown revision, RevId:" + hex(revid))


		id=devid[0]
		if id in ids:
			self.id=id
			(desc,trev,flash,ram, pe)=ids[id]
			self.descId=desc
			self.rev=devid[1]
			self.descRev=revtable(trev, self.rev)
			self.flash=flash
			self.ram=ram
			self.programmingExecutive=pe
		else:
			self.id=0
			self.descId="Unknown chip"
			self.rev=0
			self.descRev="Unknown revision"
			self.flash=0
			self.ram=0
			programmingExecutive=0

	def fullDesc(self):
		"""Generates a human-readable chip description"""
		cad=self.descId + " - " + self.descRev + " - Flash:" + str(self.flash/1024.0) + "K RAM:" + str(self.ram/1024.0) + "K PE:" + str(self.programmingExecutive/1024.0) +"K"
		return cad



