

# for each page
# Given list of dhs
dhs = []
# and talmud lines
talmud_lines = []

for dh in dhs:
    # if len(dh) > len(line)
    #foreach line on the page
        #join to next line(s) until X longer than dibburei hamatchil
        # given first_line_ref
        first_line_ref = Ref(...)
        next_line_ref = first_line_ref.next_segment_ref()
        range_ref = first_line_ref.to(next_line_ref)
        range_ref.text("he").ja().flatten_to_string()
    # try each