import socket
import json

from rlgym_sim.utils.gamestates import GameState

UDP_IP = "127.0.0.1"
UDP_PORT = 9273 # Default RocketSimVis port

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP

def write_physobj(physobj):
	j = {}
	
	j['pos'] = physobj.position.tolist()
	j['forward'] = physobj.forward().tolist()
	j['up'] = physobj.up().tolist()
	j['vel'] = physobj.linear_velocity.tolist()
	j['ang_vel'] = physobj.angular_velocity.tolist()
	
	return j

def write_car(player):
	j = {}
	
	j['team_num'] = int(player.team_num)
	j['phys'] = write_physobj(player.car_data)
	
	j['boost_amount'] = player.boost_amount * 100
	j['on_ground'] = bool(player.on_ground)
	j['is_demoed'] = bool(player.is_demoed)
	j['has_flip'] = bool(player.has_flip)

	return j

def send_state_to_rocketsimvis(gs: GameState):
	j = {}
	
	# Send ball
	j['ball_phys'] = write_physobj(gs.ball)
	
	# Send cars
	j['cars'] = []
	for player in gs.players:
		j['cars'].append(write_car(player))

	# Send boost pad states
	j['boost_pad_states'] = gs.boost_pads.tolist()

	sock.sendto(json.dumps(j).encode('utf-8'), (UDP_IP, UDP_PORT))