def create_header(file, audio_file_name, key_count, hp=8, od=8):
    file.write(f'''
osu file format v14

[General]
AudioFilename: {audio_file_name}
AudioLeadIn: 0
PreviewTime: 0
Countdown: 0
SampleSet: Soft
StackLeniency: 0.7
Mode: 3
LetterboxInBreaks: 0
SpecialStyle: 0
WidescreenStoryboard: 1

[TimingPoints]
0,500,4,2,0,100,1,0

[Difficulty]
CircleSize:{key_count}
HPDrainRate:{hp}
OverallDifficulty:{od}\n''')  # TimingPoints has some randon values


def start_note_section(file):
    file.write('[HitObjects]\n')


def create_RN(file, key_count, lane_index, start_time):  # regular note
    file.write(
        f'{int(512 / key_count * lane_index - 512 / key_count / 2)},192,{start_time},1,0,0:0:0:0:\n')
    # I'm not sure if this is correct


def create_LN(file, key_count, lane_index, start_time, end_time):  # long note
    file.write(
        f'{int(512 / key_count * lane_index - 512 / key_count / 2)},192,{start_time},128,0,{end_time}:0:0:0:0:\n')
