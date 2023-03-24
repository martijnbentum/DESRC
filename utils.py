import block
import experiment as e
import glob
import numpy as np
import os
import path
import pickle
import session

'''general functions, not specific to an object

There are likely many functions now defined on objects that should be here
Work In Progress
'''
all_block_names = open(path.data + 'all_block_names.txt').read().split('\n')

exptype2explanation_dict = {'o':'read-aloud-books','k':'News-broadcast','ifadv':'dialogue'}

def name2pp_id(name):
	'''Extract pp id from name (windower.make_name(b)).'''
	return int(name.split('_')[0].strip('pp'))

def name2exp_type(name):
	'''Extract exp type from name (windower.make_name(b)).'''
	return name.split('_')[1].strip('exp-')

def name2bid(name):
	'''Extract block id from name (windower.make_name(b)).'''
	return int(name.split('_')[2].strip('bid-'))

def load_block_with_uncorrected_artifacts(name, fo = None):
	pp_id = name2pp_id(name)
	exp_type = name2exp_type(name)
	bid = name2bid(name)
	s = session.Session(pp_id,exp_type,fo)
	vmrk = s.vmrk
	log = s.log
	return block.block(s.pp_id,s.exp_type,s.vmrk,s.log,bid,fo,corrected_artifacts = False)

def name2block(name, fo = None):
	'''Based on the name made by the windower object, create and return the block object.'''
	pp_id = name2pp_id(name)
	exp_type = name2exp_type(name)
	bid = name2bid(name)

	p = e.Participant(pp_id,fid2ort = fo)
	p.add_session(exp_type)
	s = getattr(p,'s'+exp_type)
	return getattr(s,'b'+str(bid))
	

def bad_epoch2block(be,fo = None):
	'''Return block object that correspond to the bad_epoch.'''
	p = e.Participant(be.pp_id,fid2ort = fo)
	p.add_session(be.exp_type)
	s = getattr(p,'s' + be.exp_type)
	return getattr(s, 'b' + str(be.bid))

def compute_overlap(start_a,end_a,start_b, end_b):
	'''compute the percentage b overlaps with a.
	if overlap = 1, b is equal in length or larger than a and start before or at the same time as a and
	b end later or ate the same time as a.
	'''
	# print(start_a,end_a,start_b,end_b)
	if end_a < start_a:
		raise ValueError('first interval is invalid, function assumes increasing intervals',start_a,end_a)
	if end_b < start_b:
		raise ValueError('second interval is invalid, function assumes increasing intervals',start_b,end_b)
	if end_b <= start_a or start_b >= end_a: return 0 # b is completely before or after a
	elif start_a == start_b and end_a == end_b: return end_a - start_a # a and b are identical
	elif start_b < start_a: # first statement already removed b cases completely before a
		if end_b < end_a: return end_b - start_a # b starts before a and ends before end of a	
		else: return end_a - start_a # b starts before a and ends == or after end of a
	elif start_b < end_a: # first statement already romve b cases completely after a
		if end_b > end_a: return end_a - start_b # starts after start of a and ends == or after end of a
		else: return end_b - start_b  # b starts after start of a and ends before end of a #
	else:  print('error this case should be impossible')

def load_ch_names():
	return open(path.data + 'channel_names.txt').read().split('\n')

def load_selection_ch_names():
	return [ch for ch in open(path.data + 'channel_names_selection.txt').read().split('\n') if ch]

def load_100hz_numpy_block(name):
	return np.load(path.eeg100hz + name + '.npy')

exptype2int = {'o':1,'k':2,'ifadv':3}
annot2int = {'clean':0,'garbage':1,'unk':2,'drift':3,'other':4}

def make_attributes_available(obj, attr_name, attr_values,add_number = True,name_id = '',verbose = False):
	'''make attribute available on object as a property
	For example if attr_name is 'b' attr_value(s) can be accessed as: .b1 .b2 .b3 etc.

	Keywords:
	obj = the object the attributes should be added to
	attr_name = is the name the attributes should accessed by (see above)
	attr_values = list of values (e.g. a list of block objects)
	'''
	if type(attr_values) != list:
		# values should be provided in a list
		print('should be a list of value(s), received:',type(attr_values))
		return 0
	if len(attr_values) == 0:
		# Check for values
		print('should be a list with at leat 1 item, received empty list',attr_values)
		return 0

	# Make property name
	if add_number:
		# Add a number to the property name: .b1,.b2 etc.
		if verbose:
			print('Will add a number to:',attr_name,' for each value 1 ... n values')
		if name_id != '':
			print('Number is added to property, name id:',name_id,' will be ignored')
		if len(attr_values) > 1:
			property_names = [attr_name +str(i) for i in range(1,len(attr_values)+ 1)]
		else: property_names = [attr_name + '1']

	elif len(attr_values) > 1:
		print('add_number is False: you should only add one value otherwise you will overwrite values')
		return 0

	else:
		# Add name_id to property name
		if hasattr(obj,attr_name + name_id):
			print('object already had attribute:',attr_name,' will overwrite it with new value')
			print('Beware that discrepancies between property:', attr_name, ' and list of objects could arise')
			print('e.g. .pp1 could possibly not correspond to .pp[0]')
		property_names = [attr_name+name_id]

	# add value(s) to object 
	[setattr(obj,name,attr_values[i]) for i,name in enumerate(property_names)]

	#Add list of attribute names to object
	pn = 'property_names'
	if not attr_name.endswith('_'): pn = '_' + pn

	if hasattr(obj,attr_name + pn) and not add_number:
		# if no number the list of attribute names could already excist
		getattr(obj,attr_name + pn).extend(property_names)
	else:
		# otherwise create the list
		setattr(obj,attr_name + pn,property_names)

	if verbose:
		print('set the following attribute names:')
		print(' - '.join(property_names))


def make_events(start_end_sample_number_list):
	'''Make np array compatible with MNE EEG toolkit.

	assumes a list of lists with column of samplenumbers and a column of ids  int

	structure:   samplenumber 0 id_number
	dimension 3 X n_events.
	WORK IN PROGRESS
	'''
	if set([len(line) for line in start_end_sample_number_list]):
		return np.asarray(output)	


def get_path_blockwavname(register, blockwav_name ):
	'''Return wavname corresponding to register and blockwav_name.

	blockwav_name is the filename of the experiment audio file.
	'''
	print(register,blockwav_name)
	if register == 'spontaneous_dialogue':
		p = path.data +'EEG_study_ifadv_cgn/IFADV/'
	elif register== 'read_aloud_stories':
		p = path.data + 'EEG_study_ifadv_cgn/comp-o/'
	elif register == 'news_broadcast':
		p = path.data + 'EEG_study_ifadv_cgn/comp-k/'
	else: raise Exception('Unknown register:',register)

	blockwav_path = p + blockwav_name
	return blockwav_path


def get_path_fidwav(register, fid):
	'''Return wavname corresponding to register and file id.'''
	if register == 'spontaneous_dialogue':
		path = '/Users/Administrator/storage/EEG_study_ifadv_cgn/IFADV/'
	elif register== 'read_aloud_stories':
		path = '/Users/Administrator/storage/cgn_audio/comp-o/nl/'
	elif register == 'news_broadcast':
		path = '/Users/Administrator/storage/CGN/comp-k/'
	else: raise Exception('Unknown register:',register)

	fn = glob.glob(path + fid + '*')
	if len(fn) == 1: wavname = fn[0]
	else:
		print('Could not find:',fn,' in:',path)
		return ''
	return path + wavname


def get_start_end_times_relative2blockwav(b, item, sf=1000):
	'''Return start end times of item in relation to blockwav.

	Samplenumbers are relative to start experimental audio file
	for both comp-o and comp-k multiple corpus audiofiles were used
	to create the experimental audio file.

	sample frequency = 1000
	'''
	start_block = b.st_sample
	start_time = item.st_sample
	
	end_time = item.et_sample

	start_sec = (start_time - start_block) / sf 
	end_sec = (end_time - start_block) / sf
	
	return start_sec,end_sec


def extract_audio(b, item, filename = 'default_audio_chunk'):
	'''Extract part from audio file.

	part is specified by item, can be word, chunk or sentence
	block info is needed to find times relative to onset experimental audio file.
	
	wave currently has has a namespace clash with local chunk
	wave imports chunk and my local chunk takes precedence.
	'''
	import sys
	save_path = sys.path[:]
	sys.path.remove('')
	import wave
	sys.path = save_path

	if not filename.endswith('.wav'): filename += '.wav'
	wavname = get_path_blockwavname(b.register, b.wav_filename)
	start,end = get_start_end_times_relative2blockwav(b, item)
	print('Audio name:',wavname,'start/end:',start,end)

	audio = wave.open(wavname,'rb')
	framerate = audio.getframerate()
	nchannels = audio.getnchannels()
	sampwidth = audio.getsampwidth()

	audio.setpos(int(start * framerate))
	chunk = audio.readframes(int((end-start) * framerate))

	chunk_audio = wave.open(filename,'wb')
	chunk_audio.setnchannels(nchannels)
	chunk_audio.setsampwidth(sampwidth)
	chunk_audio.setframerate(framerate)
	chunk_audio.writeframes(chunk)
	chunk_audio.close()
	print('Extracted from:',wavname,'start/end:',start,end,'written to:',filename)
	del wave

def n400_channel_set():
	return 'C3,C4,Cz,CP5,CP1,CP2,CP6,P7,P3,Pz,P4,P8,O1,O2'.split(',')

def pmn_channel_set():
	return 'Fz,F3,F7,FC5,FC1,C3,T7,CP5,CP1,Pz,P3,P7,O1,O2,P4,P8,CP6,CP2,Cz,C4,T8,FC6,FC2,F4,F8'.split(',')

def remove_channels(raw,keep_channels, remove_bads = True):
	data = raw[:][0] * 10 **6
	ch_names = load_ch_names()
	print('all',ch_names,'\nkeep',keep_channels)
	remove_ch = [n  for n in ch_names if n not in keep_channels]
	if remove_bads: remove_ch.extend(raw.info['bads'])
	print('remove',remove_ch,'\nkeep',keep_channels)
	ch_mask = [n not in remove_ch for n in ch_names]
	print(ch_mask)
	ch_names= [n for n in ch_names if not n in remove_ch]
	print('channels:',' '.join(ch_names))
	print('removed channels:', ' '.join(remove_ch))
	return data[ch_mask,:], ch_names, remove_ch

def raw2np(raw,keep_channels, remove_bads = True):
	d, ch, rm_ch = remove_channels(raw,keep_channels,remove_bads)
	return d, ch, rm_ch

def channels2indices(channels, channels_set = []):
	if channels_set == []: ch_names = load_ch_names()
	indices = []
	for i,ch in enumerate(ch_names):
		if ch in channels: indices.append(i)
	return indices

def extract_section_eeg_data(data,start,end):
	return data[:,start:end]

def extract_word_eeg_data(data,word, epoch_type = 'epoch', threshold = 75):
	if epoch_type in ['epoch','epochn400','epochpmn']:
		st = word.st_epoch - word.sample_offset 
		et = word.et_epoch - word.sample_offset 
	elif epoch_type == 'word':
		st = word.st_sample - word.sample_offset 
		et = word.et_sample - word.sample_offset 
	elif epoch_type in ['baseline','baseline_n400','baseline_pmn']:
		st = word.st_sample - 150 - word.sample_offset 
		et = word.st_sample - word.sample_offset 
	elif epoch_type == 'n400':
		st = word.st_sample + 300 - word.sample_offset 
		et = word.st_sample + 500 - word.sample_offset 
	elif epoch_type == 'pmn':
		st = word.st_sample + 250 - word.sample_offset 
		et = word.st_sample + 350 - word.sample_offset 
	else: 
		print('unknown epoch type, select from following options: epoch word baseline n400',epoch_type)
		return False
	if st < 0 or et > data.shape[1]: 
		print('word is outside eeg data:\n',word.__repr__(),'\n')
		return False
	d = extract_section_eeg_data(data, st, et)
	if d.shape[0] == 0: 
		print('eeg empty',d.shape)
		return False
	if np.max(d) > 75 or np.min(d) < -75:
		print('eeg exceeds threshold',threshold)
		return False
	return d

def make_n400_name(b,word_index):
	return b.name + '_' + '-'.join(b.sids) + '_wi-'+ str(word_index)

def save_n400_words(b, force_save = False):
	if not hasattr(b,'extracted_eeg'): b.extract_words(epoch_type = 'epochn400')
	for i,eeg in enumerate(b.extracted_eeg):
		directory = path.n400_words + 'PP' + str(b.pp_id) + '/'
		if not os.path.isdir(directory): os.mkdir(directory)
		name = directory + make_n400_name(b, b.word_indices[i])
		if os.path.isfile(name) and not force_save: continue
		np.save(name,eeg)

def make_n400_word2surprisal(overwrite= True,filename = ''):
	if filename == '': filename = path.data + 'n400word2surprisal'
	if overwrite: open(filename,'w')
	p = e.Participant(1)
	fo = p.fid2ort
	for i in range(1,49):
		p = e.Participant(i,fo)
		p.add_all_sessions()
		for s in p.sessions:
			for b in s.blocks:
				for i,w in enumerate(b.words):
					line = make_n400_name(b, i) 
					if not hasattr(w,'ppl'): line += '\t'+'NA' + '\n'
					else: 
						line += '\t'+str(w.ppl.logprob) + ',' + str(w.ppl.logprob_register) 
						line += ',' + str(w.ppl.logprob_other1) + ',' + str(w.ppl.logprob_other2) + '\n'
					with open(filename,'a') as fout:
						fout.write(line)

def n400_word2surprisal_dict(filename = ''):
	if filename == '': filename = path.data + 'n400word2surprisal'
	return dict([line.split('\t') for line in open(filename).read().split('\n') if line])

def surprisal_distribution_per_register(p):
	sk,so,sifadv = [], [], []
	skc, soc, sifadvc = [], [], []
	alls, allsc = [], []
	ninf = 0
	for s in p.sessions:
		for b in s.blocks:
			for w in b.words:
				if not hasattr(w,'ppl'): continue
				if '-inf' in w.ppl.word_line: 
					lp = -10
					ninf += 1
				else: lp = float(w.ppl.logprob)
				if 'exp-k' in b.name:
					sk.append(lp)
					if w.pos.content_word: skc.append(lp)
				if 'exp-o' in b.name:
					so.append(lp)
					if w.pos.content_word: soc.append(lp)
				if 'exp-ifadv' in b.name:
					sifadv.append(lp)
					if w.pos.content_word: sifadvc.append(lp)
				alls.append(lp)
				if w.pos.content_word: allsc.append(lp)
	return sk, so, sifadv, skc, soc, sifadvc, alls, allsc, ninf

def make_averages(fn = [], sd = {}, pp_split = False,save = False):
	if fn == []: fn = get_n400fn()
	if sd == {}: sd = n400_word2surprisal_dict()
	avg = dict()
	counter = dict()
	not_found = []
	for i,f in enumerate(fn):
		if i % 100 == 0: print(i,len(fn))
		eeg = np.load(f)
		name = f.split('/')[-1].split('.')[0]
		if name not in sd.keys():
			not_found.append(name)
			continue
		lp_names = 'lp,lp_register,lp_other1,lp_other1'.split(',') 
		lp_values = map(float,sd[name].split(','))
		for i,lp in enumerate(lp_values):
			avg_type = lp_names[i] +'_'
			if lp < -3.5: avg_type += 'high'
			elif lp > -2: avg_type += 'low'
			else:  avg_type += 'middle'
			if 'exp-k' in f: avg_type += '-k'
			elif 'exp-o' in f: avg_type += '-o'
			else: avg_type += '-ifadv'
			if pp_split: avg_type += '-'+name.split('_')[0]
			if avg_type not in avg.keys(): 
				avg[avg_type] = eeg
				counter[avg_type] = 1
			else: 
				avg[avg_type] += eeg 
				counter[avg_type] += 1
			alls = avg_type.split('-')[0] + '-alls'
			if pp_split: alls += '-'+name.split('_')[0]
			if alls not in avg.keys():
				avg[alls] = eeg
				counter[alls] = 1
			else:
				avg[alls] += eeg 
				counter[alls] += 1
	if save: 
		save_n400_dict(avg,counter)
	return avg, counter, not_found
			

def save_n400_dict(avg,counter):
	'''Save avgerage and counder in a pickle to the datasets directory.'''
	fout = open(path.datasets + 'avg_n400.dict','wb')
	pickle.dump(avg,fout,-1)
	fout.close()
	fout = open(path.datasets + 'counter_n400.dict','wb')
	pickle.dump(counter,fout,-1)
	fout.close()

def load_n400_dict():
	'''Load the average and counter dictionary.'''
	fin = open(path.datasets + 'avg_n400.dict','rb')
	avg = pickle.load(fin)
	fin.close()
	fin = open(path.datasets + 'counter_n400.dict','rb')
	counter = pickle.load(fin)
	fin.close()
	return avg, counter

	
def get_n400fn():
	fn = []
	for i in range(1,49):
		directory = path.n400_words + 'PP' + str(i) + '/'
		if not os.path.isdir(directory): 
			print(directory,'not found')
		else: fn.extend(glob.glob(directory + 'pp*.npy'))
	return fn

def load_dict_wordtype2freq():
	return dict([line.split('\t') for line in open(path.data + 'word_types_all.ft','r').read().split('\n')])


def make_word_code(word, dirty = False):
	if dirty: return word.fid + '_' + word.sid + '_' + str(word.chunk_number) + '_' + str(word.word_number) + '_' + word.word_utf8_nocode_nodia()
	return word.fid + '_' + word.sid + '_' + str(word.chunk_number) + '_' + str(word.word_number) + '_' + str(word.pos.sentence_number) + '_' + word.pos.token_number +'_' + word.word_utf8_nocode_nodia()

def load_dict_word_code2pmn_index():
	return dict([line.split('\t') for line in open(path.data + 'word_code2pmn_wi_dict').read().split('\n')])

def word2pmn_index(word):
	d = load_dict_word_code2pmn_index()
	word_code = make_word_code(word)
	return d[word_code]

def save_n400_words(b, force_save = False):
	if not hasattr(b,'extracted_eeg'): b.extract_words(epoch_type = 'epochn400')
	for i,eeg in enumerate(b.extracted_eeg):
		directory = path.n400_words + 'PP' + str(b.pp_id) + '/'
		if not os.path.isdir(directory): os.mkdir(directory)
		name = directory + make_n400_name(b, b.word_indices[i])
		if os.path.isfile(name) and not force_save: continue
		np.save(name,eeg)

def make_pmn_name(b,word_index):
	return b.name + '_' + '-'.join(b.sids) + '_wi-'+ str(word_index)

def save_pmn_words(b,content_word = False,force_save = False, dirty = False):
	if not dirty:
		if not hasattr(b,'xml') or b.xml.usability not in ['great','ok','mediocre']:
			with open(path.data + 'pmn_skipped_blocks','a') as fout:
				fout.write(b.name +'\n')
			return
	if b.st_sample == None or b.et_sample == None: return
	pmn_index_dict = load_dict_word_code2pmn_index()
	if not hasattr(b,'extracted_eeg'): b.extract_words(epoch_type = 'epochpmn',content_word = content_word, dirty = dirty)
	if not hasattr(b,'extracted_eeg'): return
	for i,eeg in enumerate(b.extracted_eeg):
		pmn_name = make_pmn_name(b,b.word_indices[i])
		w = b.extracted_words[i]
		word_code = make_word_code(w,dirty)
		if dirty: pmn_index = 'unk_pmn_index'
		else: pmn_index = pmn_index_dict[word_code]

		if dirty: directory = path.pmn_words_dirty + 'PP' + str(b.pp_id) + '/'
		else: directory = path.pmn_words+ 'PP' + str(b.pp_id) + '/'

		if not os.path.isdir(directory): os.mkdir(directory)
		if not dirty:
			cw = 'cw' if w.pos.content_word else 'nw'
		else: cw = 'unk'
		name = directory + pmn_index + '_' + word_code + '_' + b.exp_type + '_' + cw
		if os.path.isfile(name) and not force_save: continue
		np.save(name,eeg)
		with open(name +'.ch','w') as fout:
			fout.write('\n'.join(b.ch))

def load_ipa_dict():
	'''load dict that transelates cgn phonemes to ipa phonemes.'''
	return dict([line.split(',')[1:3] for line in open(path.data + 'KALDI-CGN_kaldi_ipa-word.txt').read().split('\n') if line][1:])

def transelate_ipa(phoneme, ipa_dict= None):
	'''transelate_cgn phoneme to ipa'''
	if ipa_dict == None: ipa_dict = load_ipa_dict()
	return ipa_dict[phoneme]

