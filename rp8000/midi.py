import time
import rtmidi
import re

class SysEx:

	def __init__(self, model):
		""" checks if supported model. Sets up rtmidi object. If RP8000mk2 we send startup sequence """
		self.model = model
		assert self.model == "RP8000" or  self.model == "RP8000mk2", "Only values 'RP8000' and 'RP8000mk2' are supported"
		
		self.midiout = rtmidi.MidiOut()

		if self.model == "RP8000mk2": self.startup()
		if self.model == "RP8000":    self.set_tempo(000)

	def get_port_id(self):
		""" enumerate all midi devices, rtmidi doesn't have a call by name method """
		for port, name in enumerate(self.midiout.get_ports()):
			print(port, name)
			if re.search(self.model,name):
				return port
		else:
			assert False, "No MIDI port found for %s" % self.model

	def send_message(self, message):
		""" takes a list of lists. rtmidi takes a list, we just store a few of those for multi-message messages """
		self.midiout.open_port(self.get_port_id())
		for message in message:
			print("sending: %s" % message)
			self.midiout.send_message(message)
		self.midiout.close_port()

	def set_tempo(self, tempo, channel=1):
		"""
		sets the display to the desired tempo 
		MK1 has a hardware limit of 199.9. Numbers above 199.9 continue to show a 1 in the 100s place

		"""
		# https://reverseengineering.stackexchange.com/a/25163/33391
		v = int(100 * tempo)
		b1 = (v >> 12) & 15
		b2 = (v >> 8) & 15
		b3 = (v >> 4) & 15
		b4 = (v & 15)
		channel = 16 + channel
		message = [
			0xF0    # start of SysEx
			, 0x00  # Serato manufacturer ID
			, 0x20  # Serato manufacturer ID
			, 0x7F  # Serato manufacturer ID
			, channel  # Signal BPM Channel
			, 0x00  # Signal BPM Change
			, 0x00  # Also a tempo value byte
			, b1    # byte 1
			, b2    # byte 2
			, b3    # byte 3
			, b4    # byte 4
			, 0xF7  # end of SysEx
		]

		self.send_message([message])
		
	def startup(self):
		self.send_message([	
			[0xF0,0x00,0x20,0x7F,0x01,0xF7] # triggers you to pick a MIDI channel if it's not already set and enables display
			# also sent on startup, unknown significance
			#, [0xF0,0x08,0x00,0x00,0xF7]
			#, [0xF0,0x00,0x20,0x7F,0x02,0x03,0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xF7] # enable channel 2
			, [0xF0,0x00,0x20,0x7F,0x01,0x03,0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xF7] # enable channel 1
			#, [0xF0,0x00,0x20,0x7F,0x04,0x03,0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xF7] # enable channel 4
			#, [0xF0,0x00,0x20,0x7F,0x03,0x03,0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xF7] # enable channel 3
		])
		self.send_message([	
			[0xF0,0x00,0x20,0x7F,0x01,0xF7] # triggers you to pick a MIDI channel if it's not already set and enables display
			# also sent on startup, unknown significance
			#, [0xF0,0x08,0x00,0x00,0xF7]
			, [0xF0,0x00,0x20,0x7F,0x02,0x03,0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xF7] # enable channel 2
			#, [0xF0,0x00,0x20,0x7F,0x01,0x03,0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xF7] # enable channel 1
			#, [0xF0,0x00,0x20,0x7F,0x04,0x03,0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xF7] # enable channel 4
			#, [0xF0,0x00,0x20,0x7F,0x03,0x03,0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xF7] # enable channel 3
		])

	def tempo_mode(self):
		"""
		MK1 - sets the MK1 to dislay tempo mode 
		MK2 - this sequence gets sent when pressing the tempo button. but this will not update the MK2 screen 
		"""
		## MK1 update display to tempo mode. This code is sent during Serato startup
		self.send_message([
	  		[0xF0,0x08,0x01,0x02,0x00,0x01,0xF7]
			, [0xF0,0x08,0x01,0x02,0x01,0x01,0xF7]
			, [0xF0,0x08,0x01,0x02,0x02,0x01,0xF7]
			, [0xF0,0x08,0x01,0x02,0x03,0x01,0xF7]
			, [0xF0,0x08,0x01,0x02,0x03,0x01,0xF7]
		])

		## MK2 update display code sent by Serato when you hit the physical button. This seemingly has no effect
		#self.send_message([
		#	[0xF0,0x00,0x20,0x7F,0x14,0x00,0x00,0x00,0x00,0x00,0x05,0xF7]
		#	, [0xF0,0x00,0x20,0x7F,0x13,0x00,0x00,0x00,0x00,0x00,0x05,0xF7]
		#	, [0xF0,0x00,0x20,0x7F,0x12,0x00,0x00,0x00,0x00,0x00,0x05,0xF7]
		#	, [0xF0,0x00,0x20,0x7F,0x11,0x00,0x00,0x00,0x00,0x00,0x05,0xF7]
		#])

	def time_mode(self):
		""" MK2 only - this sequence gets sent when turning display to --:-- / time mode. Unknown significance """
		self.send_message([
			[0xF0,0x00,0x20,0x7F,0x04,0x04,0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xF7]
			, [0xF0,0x00,0x20,0x7F,0x01,0x04,0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xF7]
			, [0xF0,0x00,0x20,0x7F,0x02,0x04,0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xF7]
			, [0xF0,0x00,0x20,0x7F,0x03,0x04,0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xF7]
		])

	def shutdown(self):
		"""
		this sequence is sent when Serato shuts down, it automagically disables the display mode change button
		and puts the turntable back into pitch display mode
		"""
		self.send_message([
			[0xF0,0x00,0x20,0x7F,0x02,0xF7]
		])

