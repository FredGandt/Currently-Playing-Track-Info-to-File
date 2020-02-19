# Copyright (C) 2009 - Kyle Florence
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.
#
############################################################################
# The following code, and the plugin of which it is part, is significantly #
# different to the original to which the above licence applies.            #
# An MIT licence was added to the original repository some time after the  #
# original file containing the above licence was published.                #
# I, Fred Gandt, the writer of this modification, am no legal expert, and  #
# have no idea which licence now applies, but include both.                #
############################################################################

from re import sub, split, match, fullmatch, IGNORECASE
from gi.repository import GObject, Peas, RB
from os import path as ospath, remove
from datetime import datetime
from json import load, dump

class CPTI2F (GObject.Object, Peas.Activatable):
	object = GObject.property(type=GObject.Object)
	
	def __init__(self):
		super(CPTI2F, self).__init__()
		
	def do_activate(self):
		print("Waking up the hamsters...")
		self.PATH = ospath.dirname(ospath.realpath(__file__))
		self.PLAYER = self.object.props.shell_player
		
		############ DO NOT EDIT THESE CONFIGURATION SETTINGS ############
		# EDIT config.txt IN THE SAME FOLDER YOU FOUND THIS FILE INSTEAD #
		
		self.DEFAULT_CONFIG = {
			"cache_config": False,
			"cache_format": False,
			"cache_custom_props": False,
			"artist_fallback_empty": True,
			"artist_fallback_unknown": True,
			"output_txt": True,
			"output_txt_record_limit": 5,
			"output_txt_record": "overwrite",
			"output_txt_maintenance": "keep",
			"output_default_txt": "",
			"output_json": True,
			"output_json_record_limit": 5,
			"output_json_record": "prepend",
			"output_json_maintenance": "keep",
			"output_json_record_pretty": "tab",
			"output_json_record_exclude_paths": True, # BEWARE: See config.txt
			"paths": {
				"format_path": ospath.join(self.PATH, "format.txt"),
				"custom_props_path": ospath.join(self.PATH, "custom-props.txt"),
				"output_txt_path": ospath.join(ospath.expanduser("~"), "Documents", "rhythmbox-track-info.txt"),
				"output_json_path": ospath.join(ospath.expanduser("~"), "Documents", "rhythmbox-track-info.json")
			}
		}
		
		##################################################################
		
		self.config = None
		config = self.read_config()
		# print("config:", config) # debugging only; verbose
		self.form_info = None
		self.known_entry = None
		self.custom_props = None
		self.txt_record = config["output_txt_record"]
		self.pc_id = self.PLAYER.connect("playing-changed", self.collate_track_info)
		self.psc_id = self.PLAYER.connect("playing-song-changed", self.collate_track_info)
		self.pspc_id = self.PLAYER.connect("playing-song-property-changed", self.collate_track_info)
		self.collate_track_info()
		print("Configuration achieved")
		
	def read_config(self):
		config_path = ospath.join(self.PATH, "config.txt")
		if not ospath.exists(config_path):
			print("Config file not where expected; using default settings")
		config = self.scrape_lines(self.get_file_lines(config_path), self.DEFAULT_CONFIG.copy())
		if config["cache_config"]:
			self.config = config
		return config
		
	def get_file_lines(self, path, fb={}, line=None):
		if not ospath.exists(path):
			return fb
		with open(path, "r") as f:
			lines = f.readlines()
			return lines if line is None else lines[line]
			
	def scrape_lines(self, lines, d, c=True):
		for line in lines:
			m = match(r"([a-z_]+)\=(.*)", line, flags=IGNORECASE)
			if m is not None:
				k = m.group(1)
				v = m.group(2)
				if len(v):
					if c:
						if self.is_path_prop(k):
							d["paths"][k] = v
						else:
							m = fullmatch(r" *(?:(?:(true)|false)|([0-9]+)|([0-9]+\.[0-9]+)) *", v, flags=IGNORECASE)
							if m is not None:
								g2 = m.group(2)
								g3 = m.group(3)
								v = int(g2) if g2 is not None else (float(g3) if g3 is not None else (True if m.group(1) is not None else False))
							d[k] = v
					else:
						d["custom_" + k] = v
		return d
		
	def is_path_prop(self, p):
		return fullmatch(r"[a-z_]+_path", p) is not None
		
	def collate_track_info(self, *args):
		entry = self.PLAYER.get_playing_entry()
		if self.is_playing() and entry is not None and entry != self.known_entry:
			output_txt, output_json = self.configs_get("output_txt", "output_json")
			if not output_txt and not output_json:
				print("Both txt and json output settings in config are false; nothing to do")
				return
			print("Collating new track info...")
			self.known_entry = entry
			pt = RB.RhythmDBPropType
			props_by_type = {
				"str_props": {
					"title": pt.TITLE,
					"album": pt.ALBUM,
					"genre": pt.GENRE,
					"artist": pt.ARTIST,
					"comment": pt.COMMENT,
					"summary": pt.SUMMARY,
					"subtitle": pt.SUBTITLE,
					"composer": pt.COMPOSER,
					"copyright": pt.COPYRIGHT,
					"media_type": pt.MEDIA_TYPE,
					"description": pt.DESCRIPTION,
					"album_artist": pt.ALBUM_ARTIST,
					"last_played_str": pt.LAST_PLAYED_STR
				},
				"ulong_props": {
					"year": pt.YEAR,
					"bitrate": pt.BITRATE, # in kbps
					"disc_num": pt.DISC_NUMBER,
					"play_count": pt.PLAY_COUNT,
					"track_length": pt.DURATION, # in seconds
					"discs_total": pt.DISC_TOTAL,
					"track_num": pt.TRACK_NUMBER,
					"last_played": pt.LAST_PLAYED, # in seconds
					"tracks_total": pt.TRACK_TOTAL
				},
				"double_props": {
					"rating": pt.RATING, # presumably of 5?
					"bpm": pt.BEATS_PER_MINUTE
					# no longer supported :(
						#"replaygain_album_gain": pt.REPLAYGAIN_ALBUM_GAIN
						#"replaygain_album_peak": pt.REPLAYGAIN_ALBUM_PEAK
						#"replaygain_track_gain": pt.REPLAYGAIN_TRACK_GAIN
						#"replaygain_track_peak": pt.REPLAYGAIN_TRACK_PEAK
				}
			}
			txt_props = {}
			json_props = {
				"str_props": {},
				"ulong_props": {},
				"double_props": {}
			}
			for prop_type, props_to_get in props_by_type.items():
				for k, v in props_to_get.items():
					str_type = prop_type == "str_props"
					pre_formed = self.pre_format_props(str_type, k, (
						entry.get_string(v.strip() if isinstance(v, str) else v) if str_type else
						entry.get_double(v) if prop_type == "double_props" else
						entry.get_ulong(v) if prop_type == "ulong_props" else None
					))
					formatted = pre_formed["formatted"]
					if output_txt:
						is_list = isinstance(formatted, list)
						if is_list:
							f_csv = ", ".join(formatted[:-1])
							f_le = formatted[-1]
							txt_props[k] = f_csv + " 𝘢𝘯𝘥 " + f_le if len(f_csv) > 0 else f_le
						else:
							txt_props[k] = formatted
					json_props[prop_type][k] = pre_formed if pre_formed["raw"] != formatted else formatted
			if output_json:
				# print("json properties:", json_props) # debugging only; verbose
				self.write_json_file(json_props)
			if output_txt:
				format_path, cache_format = self.configs_get("format_path", "cache_format")
				form_info = "{title} by {artist} from {album}"
				album_artist = txt_props["album_artist"]
				artist = txt_props["artist"]
				if self.fallback_artist(artist):
					txt_props["artist"] = album_artist
				if self.fallback_artist(album_artist):
					txt_props["album_artist"] = artist
				txt_props = self.get_custom_props(txt_props)
				# print("txt and custom properties:", txt_props) # debugging only; verbose
				if self.form_info is not None:
					form_info = self.form_info
				elif ospath.exists(format_path):
					form_info = self.get_file_lines(format_path, {}, 0)
					if cache_format:
						self.form_info = form_info
				self.write_txt_file(txt_props, form_info)
				
	def is_playing(self):
		return self.PLAYER.get_playing_entry() is not None
		
	def pre_format_props(self, t, k, v):
		result = {"raw": v, "formatted": v}
		if k == "track_length":
			m, s = divmod(v, 60)
			h, m = divmod(m, 60)
			if m > 0:
				if h > 0:
					result["formatted"] = "{}h:{}m:{}s".format(h, m, s)
				result["formatted"] = "{}m:{}s".format(m, s)
			else:
				result["formatted"] = "{}s".format(s)
		elif k == "bitrate":
			result["formatted"] = "{}kbps".format(v) if v > 0 else v
		elif k == "last_played":
			result["formatted"] = datetime.fromtimestamp(v).strftime("%T, %B %e, %Y") if v > 0 else "Never"
		elif t and isinstance(v, str) and (k == "artist" or k == "composer"):
			result["formatted"] = split(r"(?: *[;\\/] *)", v)
		return result
		
	def get_custom_props(self, props={}):
		custom_props_path, cache_custom_props = self.configs_get("custom_props_path", "cache_custom_props")
		custom_props = self.scrape_lines(self.get_file_lines(custom_props_path), {}, False)
		if cache_custom_props:
			if self.custom_props is None:
				self.custom_props = custom_props
			props.update(self.custom_props)
		else:
			self.custom_props = None
			props.update(custom_props)
		return props
		
	def fallback_artist(self, a):
		is_str = isinstance(a, str)
		empty, unknown = self.configs_get("artist_fallback_empty", "artist_fallback_unknown")
		return ((((is_str and len(a) == 0) or a is None) and empty) or
			(is_str and fullmatch(r"unknown", a, flags=IGNORECASE) is not None and unknown))
		
	def trim_trax(self, record, trax, limit):
		if limit is not None and limit > 1:
			while len(trax) >= limit:
				if record == "append":
					trax.pop(0)
				else:
					trax.pop()
					
	def aprehend(self, record, trax, info):
		if record == "prepend":
			trax.insert(0, info)
		else:
			trax.append(info)
			
	def write_json_file(self, json_props=None):
		config = self.config_the_config().copy()
		record = config["output_json_record"]
		path = config["paths"]["output_json_path"] # TODO: check old path if known and move file if found
		limit = config["output_json_record_limit"]
		pretty = config["output_json_record_pretty"]
		jso = {"tracks":[],"config":{"paths":{}}}
		trax = jso["tracks"]
		if limit == 1:
			record = "overwrite"
		if record != "overwrite":
			if ospath.exists(path):
				with open(path, "r") as f:
					jso = load(f) # TODO: assumes file content is good to go
				trax = jso["tracks"]
				if jso["config"]["output_json_record"] != record:
					trax.reverse()
				self.trim_trax(record, trax, limit)
		if json_props is not None:
			self.aprehend(record, trax, json_props)
		else:
			if config["output_json_maintenance"] == "delete":
				remove(path)
				return
			json_props = "No track properties"
		if config["output_json_record_exclude_paths"]:
			del config["paths"]
		config["utc_timestamp"] = datetime.utcnow().timestamp() # is this even useful?
		config["playing"] = self.is_playing()
		jso["config"] = config
		with open(path, "w") as f:
			pet = pretty == "tab"
			if isinstance(pretty, int) and pretty > 0 or pet:
				if pet:
					pretty = "\t"
				dump(jso, f, ensure_ascii=False, indent=pretty)
			else:
				dump(jso, f, separators=(",", ":"))
			print('Written to file at "{}" using "{}":\n\n{}\n'.format(path, record, json_props))
			
	def write_txt_file(self, props, to_format):
		if isinstance(to_format, str) and len(to_format):
			path, record, limit = self.configs_get("output_txt_path", "output_txt_record", "output_txt_record_limit") # TODO: check old path if known and move file if found
			info = to_format.format(**props)
			trax = []
			if limit == 1:
				record = "overwrite"
			if record != "overwrite":
				trax = self.get_file_lines(path, [])
				if self.txt_record != record:
					trax.reverse()
				self.trim_trax(record, trax, limit)
			self.aprehend(record, trax, info)
			self.txt_record = record
			with open(path, "w") as f:
				f.write("".join(trax))
				print('Written to file at "{}" using "{}":\n\n{}'.format(path, record, info))
				
	def config_the_config(self):
		return self.config if self.config is not None else self.read_config()
		
	def configs_get(self, *settings):
		config = self.config_the_config()
		return tuple(self.config_get(setting, config) for setting in settings)
		
	def config_get(self, setting, config=None):
		if config is None:
			config = self.config_the_config()
		if self.is_path_prop(setting):
			config = config["paths"]
		return config[setting]
		
	def do_deactivate(self):
		print("Putting the hamsters to bed...")
		maint, def_txt, path = self.configs_get("output_txt_maintenance", "output_default_txt", "output_txt_path")
		if maint == "default":
			self.write_txt_file(self.get_custom_props(), def_txt)
		elif maint == "delete":
			remove(path)
		self.write_json_file()
		self.PLAYER.disconnect(self.pc_id)
		self.PLAYER.disconnect(self.psc_id)
		self.PLAYER.disconnect(self.pspc_id)
		del self.DEFAULT_CONFIG
		del self.PLAYER
		del self.PATH
		del self.config
		del self.form_info
		del self.txt_record
		del self.known_entry
		del self.custom_props
		print("They're so cute when they're sleeping <3")
		
