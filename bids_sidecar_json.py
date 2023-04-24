import json

fields = 'Taskname,TaskDescription,Instructions,InstitutionName'
fields += ',SamplingFrequency,Manufacturer,ManufacturersModelName'
fields += ',CapManufacturer,CapManufacturersModelName,EEGChannelCount'
fields += ',EOGChannelCount,ECGChannelCount,EMGChannelCount'
fields += ',TriggerChannelCount,PowerLineFrequency,EEGPlacementScheme'
fields += ',EEGReference,EEGGround,SoftwareFilters,HardwareFilters'
fields += ',RecordingDuration,RecordingType'
fields = fields.split(',')


hardware_filter = {}
hardware_filter['Bandpass filter'] = {'low cutoff (hz)':0.01, 
    'high cutoff (hz)':100}
institute_name = 'Centre for Language Studies, Radboud University Nijmegen'

def make_general_eeg_sidecar():
    '''set standard values to eeg sidecar.'''
    d = {f:'n/a' for f in fields}
    d['InstitutionName'] = institute_name
    d['SamplingFrequency'] = 1000
    d['Manufacturer'] = 'Brain products'
    d['ManufacturersModelName'] = 'actiCHamp (5001)'
    d['CapManufacturer'] = 'EasyCap'
    d['CapManufacturersModelName'] = '?'
    d['EEGChannelCount'] = 26
    d['EOGChannelCount'] = 2
    d['ECGChannelCount'] = 0
    d['EMGChannelCount'] = 0
    d['TriggerChannelCount'] = 1
    d['PowerLineFrequency'] = 50
    d['EEGPlacementScheme'] = '10-20'
    d['EEGReference'] = 'left mastoid'
    d['EEGGround'] = 'placed in ground location of cap adjacent to AFz'
    d['HardwareFilters'] = hardware_filter
    return d

recording_types = 'continuous,epoched,discontinuous'.split(',')
    
def eeg_sidecar_add_values(d, recording_duration, recording_type):
    '''adds recording_duration in seconds and recording type to side car.'''
    if recording_duration < 1000:
        print(recording_duration,'duration should be in seconds')
    if recording_type not in recording_types:
        raise ValueError(recording_type,'not in', recording_types)
    d[RecordingDuration] = recording_duration
    d[RecordingType] = recording_type
    
    
    

