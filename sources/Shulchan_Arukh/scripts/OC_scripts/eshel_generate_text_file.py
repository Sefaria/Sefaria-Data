#encoding=utf-8

from sources.Shulchan_Arukh.ShulchanArukh import *

filenames = [u"../../txt_files/Orach_Chaim/part_1/שוע אורח חיים חלק א אשל אברהם.txt",
             u"../../txt_files/Orach_Chaim/part_2/שולחן ערוך אורח חיים חלק ב אשל אברהם.txt",
             u"../../txt_files/Orach_Chaim/part_3/שלחן ערוך אורח חיים חלק ג אשל אברהם מושלם.txt"]

def modify(str):
    return str.replace("[", "").replace("]", "").replace("(", "").replace(")", "")


def convert_tag(tag):
    char = numToHeb(getGematria(tag))
    return "@22{}".format(char.encode('utf-8'))

def break_up_22s(eshel_lines):
    new_lines = []
    prev_line_22 = False
    for line in eshel_lines:
        if line.startswith("@22") and len(line) > 10:
            tag, comm = line.split(" ")[0], " ".join(line.split(" ")[1:])
            if tag == "@22":
                new_lines[-1] += " " + line.replace("@22 ", "").replace("@11", "")
                continue
            tag = convert_tag(tag)
            new_lines.append(tag)
            new_lines.append(comm)
            prev_line_22 = True
        elif line.startswith("@22"):
            line = convert_tag(line)
            prev_line_22 = True
            new_lines.append(line)
        elif not prev_line_22:
            new_lines[-1] += " " + line.replace("@11", "")
        else:
            prev_line_22 = False
            new_lines.append(line)
    return new_lines



def insert_simanim(eshel_lines, base_dict):
    current_key = sorted(base_dict.keys())[0]
    current_pos = 0
    new_eshel_lines = [u"@00א"]
    current_siman = 1
    line_to_post = ""
    for i, line in enumerate(eshel_lines):
        line = line.decode('utf-8')
        matches = re.findall(u"@22(\S+)", line)
        assert len(matches) in [0, 1]
        new_eshel_lines.append(line)
        if line_to_post:
            new_eshel_lines.append(line_to_post)
            line_to_post = ""
        if len(matches) == 1:
            char = modify(matches[0])
            current_pos += 1
            if len(base_dict[current_key]) == current_pos:
                current_pos = 0
                current_key += 1
                while current_key in base_dict.keys() and base_dict[current_key] == []:
                    current_key += 1
                if current_key not in base_dict.keys():
                    continue
                line_to_post = u"@00{}".format(numToHeb(current_key))

    return new_eshel_lines


def gather_content(base):
    base_refs = []
    base_indices = [416, 458]
    base_dict = {}
    for i in range(3):
        b_vol = base.get_volume(i + 1)
        mark = "@88" if i < 2 else "@99"
        for siman in b_vol:
            base_dict[siman.num] = []
            for seif in siman:
                for char in [match.group(1) for match in seif.grab_references(mark + "(\S+)\]")]:
                    base_dict[siman.num] += [char]

    eshel_markers = []
    eshel_indices = [415, 456]
    eshel_lines = []

    for file_n, filename in enumerate(filenames):
        with open(filename) as f:
            for line_n, line in enumerate(f):
                line = line.replace("\r", "").replace("\n", "")
                if len(line) > 4:
                    eshel_lines.append(line)
                for i, char in enumerate([modify(str) for str in re.findall(u"@22(\S+)", line)]):
                    eshel_markers += [char]
    return eshel_lines, base_dict


def get_volumes():
    root = Root('../../Orach_Chaim.xml')
    base = root.get_base_text()
    return base



if __name__ == "__main__":
    base = get_volumes()
    eshel_lines, base_dict = gather_content(base)
    eshel_lines = break_up_22s(eshel_lines)
    new_eshel_lines = insert_simanim(eshel_lines, base_dict)
    new_file = open("/".join(filenames[0].split("/")[0:-1])+"/eshel_3 volumes with simanim.txt", 'w')
    for line in new_eshel_lines:
        new_file.write(line.encode('utf-8')+"\n")
    new_file.close()