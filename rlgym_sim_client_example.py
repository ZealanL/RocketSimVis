import socket
import struct
	
from rlgym_sim.utils.gamestates import GameState

UDP_IP = "127.0.0.1"
UDP_PORT = 9273

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP

def pack_vec(vec):
	return struct.pack("<f", vec[0]) + struct.pack("<f", vec[1]) + struct.pack("<f", vec[2])

def pack_physobj(physobj):
	return (
		pack_vec(physobj.position) + 
		pack_vec(physobj.forward()) + pack_vec(physobj.right()) + pack_vec(physobj.up()) + 
		pack_vec(physobj.linear_velocity) + 
		pack_vec(physobj.angular_velocity)
		)

def pack_car(player):
	bytes = b""
	
	# Team number
	bytes += struct.pack("B", int(player.team_num))
	
	# Car physics state
	bytes += pack_physobj(player.car_data)
	
	# Car boost
	bytes += struct.pack("<f", player.boost_amount)
	
	# Car demoed
	bytes += struct.pack("B", player.is_demoed)
	
	# Car controls (not implemented yet)
	bytes += struct.pack("<f", 0)
	bytes += struct.pack("B", 0)
	bytes += struct.pack("B", 0)
	bytes += struct.pack("B", 0)
	
	return bytes

def send_data_to_rsvis(gs: GameState):
	msg = b""
	
	# Prefix signature
	# This is required at the start of all packets so that RocketSimVis knows its valid data
	msg += struct.pack("I", 0xA490E7B3)
	
	# Arena tick count (not implemented)
	msg += struct.pack("I", 0)
	
	# Send cars
	msg += struct.pack("I", len(gs.players))
	for player in gs.players:
		msg += pack_car(player)
		
	# Boost pads (not implemented yet)
	msg += struct.pack("I", 0)
		
	# Send ball
	msg += pack_physobj(gs.ball)

	sock.sendto(msg, (UDP_IP, UDP_PORT))