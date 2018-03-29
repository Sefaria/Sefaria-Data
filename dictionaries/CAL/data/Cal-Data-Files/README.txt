file_structure
	bcal.txt:                   stam list of words, basic POS and dict headwords (dictfull.txt)
	dictfull.txt:               tree formatted dict entries with definitions (from multiple dicts, we're just interested in lang codes 53 and 71. NOTE: codes are appended together as strings)
	caldbfull.txt:              follows talmud. for every word defines headword (use bcal.txt to translate to dictfull.txt)
	jastrow-pages.txt:          jastrow entry, basic POS, page number
	jbaforms.txt:               forms found in talmud matched to dict headwords. also has POS info (use bcal.txt to translate to cal_definitions.txt)
	cal_definitions.txt:        looks like a filtered version of dictfull.txt. can probably ignore

dialect_codes
	categories
		0 = common aramaic
		1 = old aramaic
		2 = imperial/official aramaic
		3 = biblical aramaic
		4 = middle aramaic
		5 = palestinian aramaic
		6 = syriac
		7 = babylonian aramaic
		8 = late jewish literary aramaic

	00 = common aramaic
	00-1 = ??? common aramaic -OA
	00-1-2-3 = ??? common aramaic -OA-OfA-BA
	00-1-6 = ??? common aramaic -OA-Syr
	10 = N/A
	11 = Old Aramaic-Old Mesopotamian (OA^Mesop)
	12 = Old Aramaic from Zenjirli (OA^Zenj)
	13 = Old Aramaic-Syria (OA^Syr)
	14 = Old Aramaic-East (OA^East)
	20 = ??? OfA^Gen
	21 = ??? OfA^Mesop
	22 = ??? OfA^Eg-informal
	23 = official aramaic-egypt (OfA^Eg)
	24 = official aramaic-persia (OfA^Per)
	25 = ??? OfA^Ideog
	26 = ??? OfA^Sam
	27 = ??? OfA^East
	28 = ??? OfA^West
	31 = ??? BA^Ezra
	32 = ??? BA^Dan
	41 = Palmyrene
	42 = Nabatean
	43 = Hatran
	44 = Qumran
	45 = ParthianMidAr
	46 = SamaritanMidAr (not really a thing. found in an erroneous dialect code)
	47 = N/A
	50 = jewish palestinian aramaic original archival texts (Jud)
	51 = jewish literary aramaic of the early targumim (onkeles and jonathan to the prophets) (JLAtg)
	52 = epigraphic jewish palestinian aramaic (JPAEpig)
	53 = galilean aramaic (Gal)
	54 = palestinian targumic aramaic (PTA)
	55 = christian palestinian aramaic (CPA)
	56 = samaritan palestinian aramaic (Sam)
	60 = syriac (Syr)
	70 = babylonian magic bowl koine aramaic (BabMBK)
	71 = jewish babylonian aramaic (JBA)
	72 = gaonic babylonian aramaic
	73 = N/A
	74 = mandaic (Man)
	81 = late jewish literary aramaic (LJLA)
	82 = judaeo-syriac

parts_of_speech (dictfull.txt)
	N = noun
	X = adverb
	A = adjective
	c = conjunction
	R = pronoun
	p = preposition
	I = interjection
	b = number
	s = letter
	d = divine name
	Vxx = (see below)

parts_of_speech (caldbdull.txt)
	-----
	NOUNS                               COUNT    EXAMPLE
	-----
	N01 = singular absolute or          1286     br) N01 br
         determined
	N02 = singular determined           10405    mylt) N02 mylt)
	N03 = plural absolute               117      d_ p+zymn) N03 dzmnyN
	N04 = plural construct              187      bd_ p+br) N04 bdbny
	N05 = plural determined             2434     d_ p+qyTr) N05 dqTry

	-----
	VERBS (alternate abbreviations used in jastrow-pages.txt)
	-----
	V01 = peal = G                      16036    d_ c+npq V01 dnpqy
	V02 = pael = D                      1957     bTl V02 mbTyl
	V03 = (h)aphel  = C                 1875     l_ p02+$wy V03 l)$wyy
	V04 = ethpeel = Gt                  1302     xzy V04 mytxzy
	V05 = ethpaal = Dt                  529      tws V05 mytwwsN
	V06 = ettaphal = Ct                 56       k$r V06 )ytk$r
	V07 = pay/w(el                      0
	V08 = reduplicated                  64       TlTl V08 mTlTl
	V09 = quadriliteral = Q (4 root)    117      b$qr V09 mb$qr
	V10 = ethpaiel                      4        l_ p02+qlql V10 l)yqlqwly
	V11 = reflexive reduplicate         0
	V12 = reflexive quadriliteral = Qt  12       qlql V12 myqlql)

	----------
	ADJECTIVES
	----------
	A01 = singular absolute or          1404     d_ c+$ry A01 d$ry
          determined
	A02 = singular determined           453      m(ly A02 m(lyyt)
	A03 = plural absolute               130      d_ c+mryr A03 dmryrN
	A04 = plural construct              2        qTyl A04 qTyly
	A05 = plural determined             274      xdt A05 xdty

	---------
	NUMERICAL
	---------
	n01 = singular absolute or          816
        determined
	n02 = singular determined           506
	n03 = plural absolute               71
	n04 = plural construct              4
	n05 = plural determined             26

	-----------
	PREPOSITION
	-----------
	p01 = independent                   1115
	p02 = with pronominal suffix        7350
	p03 = proclitic

	----
	MISC
	----
	GN = Geographical Name              2
	c = conjunction                     16130
	a = adverb                          9389
	I = interjection                    487
	d = divine name                     ???
	PN = proper name                    0

	TOTAL NUM WORDS                     70042
