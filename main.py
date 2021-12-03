from pydub import AudioSegment
import os
import wave

def get_sad_ar(fileName):
    file = open(fileName)
    lines = file.read().split("\n")
    result = []
    for line in lines:
        lineEntries = line.split("\t")
        result.append([float(lineEntries[0]), float(lineEntries[1]), lineEntries[2]])  # StartTime, endTime, "speech" || "pause"
    return result

#If a silence entry is under thresh, change it into speech
def remove_short_silence(ar, thresh):
    for entry in ar:
        if entry[1] - entry[0] < thresh and entry[2] == "pause":
            entry[2] = "speech"
    return ar

#Combine sequential "speech" entries from remove_short_silence into single entries.
#Returns list of all speech segments
def compact(ar):
    to_return = []
    current_start = 0
    started = False
    for i in (range(len(ar))):
        if not started and ar[i][2] == "speech":
            started = True
            current_start = ar[i][0]
        elif started and ar[i][2] == "pause":
            to_return.append([current_start, ar[i - 1][1]])
            started = False
    if started:
        to_return.append([current_start, ar[len(ar) - 1][1]])
    return to_return


def get_major_cuts(ar, silence_buf):
    to_return = []
    for i in range(len(ar)):
        earliest_begin = 0.00 if i == 0 else (ar[i - 1][1]+ar[i][0])/2 #0 if this is the first entry, or midpoint between last entry's ending and this entry's beginning
        latest_end = ar[i][1] if i == (len(ar) - 1) else (ar[i + 1][0]+ar[i][1])/2 #End of this entry if this is the last entry, or midpoint between this ending and next entry's beginning
        to_return.append([max(earliest_begin, ar[i][0] - silence_buf), min(latest_end, ar[i][1] + silence_buf)]) #Set cut to between min(10s before beginning || midpoint between last entry's end and this one's begin) and min(10s after ending || midpoint between next entry's begin and this one's end)
    return to_return

#Split the audio in the major cuts into 10s pieces.  If a pieces is 2s or less, concatenate it with the piece before it
def do_split(segment_array, audio, prefix, minChunkSize):
    for i in range(len(segment_array)):
        sub_index = 0
        start = segment_array[i][0]
        while True:
            end = min(segment_array[i][1], start+10)
            if end + minChunkSize > segment_array[i][1]:
                end = segment_array[i][1]
            out_file_name = "{0}.chunk{1}.{2}.wav".format(prefix, i, sub_index)
            audio[start*1000:end*1000].export(out_file_name, format="wav")
            sub_index = sub_index + 1
            if end is segment_array[i][1]:
                break
            else:
                start = end

if __name__ == '__main__':
    filenames = []
    for file in os.listdir():
        if ".wav" in file:
            filenames.append(file[:len(file)-4])
    thresh = float(input("What is the minimum silence length to not be disregarded\n"))
    buf = float(input("How long should the silence buffer on the ends of speech be?\n"))
    minChunkSize = float(input("What should be the minimum length of a chunk in seconds?\n"))
    for file in filenames:
        ar = get_sad_ar(file + ".txt")
        ar = remove_short_silence(ar, thresh)
        ar = compact(ar)
        ar = get_major_cuts(ar, buf)
        audio = AudioSegment.from_wav(file + ".wav")
        do_split(ar, audio, file, minChunkSize)
