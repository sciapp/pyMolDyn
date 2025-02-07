# editorconfig-checker-disable
"""
This module includes information about the chemical elements:
- names maps element number to name
- colors maps element number to RGB color
- numbers maps element symbol to element number (not a 1:1, but a n:1
  mapping, see element 112: Ununbium/Copernicum)
- radii maps element number to covalent radius in Å (data from openbabel)
http://sourceforge.net/p/openbabel/code/HEAD/tree/openbabel/trunk/data/element.txt
"""
# editorconfig-checker-enable

import numpy as np

colors = np.zeros((120, 3), np.uint8)
radii = np.zeros(120, float)
names = np.zeros(120, object)
numbers = {}

numbers["H"] = 1
names[1] = "Hydrogen"
colors[1] = (255, 255, 255)
radii[1] = 0.31

numbers["HE"] = 2
names[2] = "Helium"
colors[2] = (217, 255, 255)
radii[2] = 0.28

numbers["LI"] = 3
names[3] = "Lithium"
colors[3] = (204, 128, 255)
radii[3] = 1.28

numbers["BE"] = 4
names[4] = "Beryllium"
colors[4] = (194, 255, 0)
radii[4] = 0.96

numbers["B"] = 5
names[5] = "Boron"
colors[5] = (255, 181, 181)
radii[5] = 0.84

numbers["C"] = 6
names[6] = "Carbon"
colors[6] = (144, 144, 144)
radii[6] = 0.76

numbers["N"] = 7
names[7] = "Nitrogen"
colors[7] = (48, 80, 248)
radii[7] = 0.71

numbers["O"] = 8
names[8] = "Oxygen"
colors[8] = (255, 13, 13)
radii[8] = 0.66

numbers["F"] = 9
names[9] = "Fluorine"
colors[9] = (144, 224, 80)
radii[9] = 0.57

numbers["NE"] = 10
names[10] = "Neon"
colors[10] = (179, 227, 245)
radii[10] = 0.58

numbers["NA"] = 11
names[11] = "Sodium"
colors[11] = (171, 92, 242)
radii[11] = 1.66

numbers["MG"] = 12
names[12] = "Magnesium"
colors[12] = (138, 255, 0)
radii[12] = 1.41

numbers["AL"] = 13
names[13] = "Aluminium"
colors[13] = (191, 166, 166)
radii[13] = 1.21

numbers["SI"] = 14
names[14] = "Silicon"
colors[14] = (240, 200, 160)
radii[14] = 1.11

numbers["P"] = 15
names[15] = "Phosphorus"
colors[15] = (255, 128, 0)
radii[15] = 1.07

numbers["S"] = 16
names[16] = "Sulfur"
colors[16] = (255, 255, 48)
radii[16] = 1.05

numbers["CL"] = 17
names[17] = "Chlorine"
colors[17] = (31, 240, 31)
radii[17] = 1.02

numbers["AR"] = 18
names[18] = "Argon"
colors[18] = (128, 209, 227)
radii[18] = 1.06

numbers["K"] = 19
names[19] = "Potassium"
colors[19] = (143, 64, 212)
radii[19] = 2.03

numbers["CA"] = 20
names[20] = "Calcium"
colors[20] = (61, 225, 0)
radii[20] = 1.76

numbers["SC"] = 21
names[21] = "Scandium"
colors[21] = (230, 230, 230)
radii[21] = 1.70

numbers["TI"] = 22
names[22] = "Titanium"
colors[22] = (191, 194, 199)
radii[22] = 1.60

numbers["V"] = 23
names[23] = "Vanadium"
colors[23] = (166, 166, 171)
radii[23] = 1.53

numbers["CR"] = 24
names[24] = "Chromium"
colors[24] = (138, 153, 199)
radii[24] = 1.39

numbers["MN"] = 25
names[25] = "Manganese"
colors[25] = (156, 122, 199)
radii[25] = 1.39

numbers["FE"] = 26
names[26] = "Iron"
colors[26] = (224, 102, 51)
radii[26] = 1.32

numbers["CO"] = 27
names[27] = "Cobalt"
colors[27] = (240, 144, 160)
radii[27] = 1.26

numbers["NI"] = 28
names[28] = "Nickel"
colors[28] = (80, 208, 80)
radii[28] = 1.24

numbers["CU"] = 29
names[29] = "Copper"
colors[29] = (200, 128, 51)
radii[29] = 1.32

numbers["ZN"] = 30
names[30] = "Zinc"
colors[30] = (125, 128, 176)
radii[30] = 1.22

numbers["GA"] = 31
names[31] = "Gallium"
colors[31] = (194, 143, 143)
radii[31] = 1.22

numbers["GE"] = 32
names[32] = "Germanium"
colors[32] = (102, 143, 143)
radii[32] = 1.20

numbers["AS"] = 33
names[33] = "Arsenic"
colors[33] = (189, 128, 227)
radii[33] = 1.19

numbers["SE"] = 34
names[34] = "Selenium"
colors[34] = (225, 161, 0)
radii[34] = 1.20

numbers["BR"] = 35
names[35] = "Bromine"
colors[35] = (166, 41, 41)
radii[35] = 1.20

numbers["KR"] = 36
names[36] = "Krypton"
colors[36] = (92, 184, 209)
radii[36] = 1.16

numbers["RB"] = 37
names[37] = "Rubidium"
colors[37] = (112, 46, 176)
radii[37] = 2.20

numbers["SR"] = 38
names[38] = "Strontium"
colors[38] = (0, 255, 0)
radii[38] = 1.95

numbers["Y"] = 39
names[39] = "Yttrium"
colors[39] = (148, 255, 255)
radii[39] = 1.90

numbers["ZR"] = 40
names[40] = "Zirconium"
colors[40] = (148, 224, 224)
radii[40] = 1.75

numbers["NB"] = 41
names[41] = "Niobium"
colors[41] = (115, 194, 201)
radii[41] = 1.64

numbers["MO"] = 42
names[42] = "Molybdenum"
colors[42] = (84, 181, 181)
radii[42] = 1.54

numbers["TC"] = 43
names[43] = "Technetium"
colors[43] = (59, 158, 158)
radii[43] = 1.47

numbers["RU"] = 44
names[44] = "Ruthenium"
colors[44] = (36, 143, 143)
radii[44] = 1.46

numbers["RH"] = 45
names[45] = "Rhodium"
colors[45] = (10, 125, 140)
radii[45] = 1.42

numbers["PD"] = 46
names[46] = "Palladium"
colors[46] = (0, 105, 133)
radii[46] = 1.39

numbers["AG"] = 47
names[47] = "Silver"
colors[47] = (192, 192, 192)
radii[47] = 1.45

numbers["CD"] = 48
names[48] = "Cadmium"
colors[48] = (255, 217, 143)
radii[48] = 1.44

numbers["IN"] = 49
names[49] = "Indium"
colors[49] = (166, 117, 115)
radii[49] = 1.42

numbers["SN"] = 50
names[50] = "Tin"
colors[50] = (102, 128, 128)
radii[50] = 1.39

numbers["SB"] = 51
names[51] = "Antimony"
colors[51] = (158, 99, 181)
radii[51] = 1.39

numbers["TE"] = 52
names[52] = "Tellurium"
colors[52] = (212, 122, 0)
radii[52] = 1.38

numbers["I"] = 53
names[53] = "Iodine"
colors[53] = (148, 0, 148)
radii[53] = 1.39

numbers["XE"] = 54
names[54] = "Xenon"
colors[54] = (66, 158, 176)
radii[54] = 1.40

numbers["CS"] = 55
names[55] = "Caesium"
colors[55] = (87, 23, 143)
radii[55] = 2.44

numbers["BA"] = 56
names[56] = "Barium"
colors[56] = (0, 201, 0)
radii[56] = 2.15

numbers["LA"] = 57
names[57] = "Lanthanum"
colors[57] = (112, 212, 255)
radii[57] = 2.07

numbers["CE"] = 58
names[58] = "Cerium"
colors[58] = (255, 255, 199)
radii[58] = 2.04

numbers["PR"] = 59
names[59] = "Praseodymium"
colors[59] = (217, 225, 199)
radii[59] = 2.03

numbers["ND"] = 60
names[60] = "Neodymium"
colors[60] = (199, 225, 199)
radii[60] = 2.01

numbers["PM"] = 61
names[61] = "Promethium"
colors[61] = (163, 225, 199)
radii[61] = 1.99

numbers["SM"] = 62
names[62] = "Samarium"
colors[62] = (143, 225, 199)
radii[62] = 1.98

numbers["EU"] = 63
names[63] = "Europium"
colors[63] = (97, 225, 199)
radii[63] = 1.98

numbers["GD"] = 64
names[64] = "Gadolinium"
colors[64] = (69, 225, 199)
radii[64] = 1.96

numbers["TB"] = 65
names[65] = "Terbium"
colors[65] = (48, 225, 199)
radii[65] = 1.94

numbers["DY"] = 66
names[66] = "Dysprosium"
colors[66] = (31, 225, 199)
radii[66] = 1.92

numbers["HO"] = 67
names[67] = "Holmium"
colors[67] = (0, 225, 156)
radii[67] = 1.92

numbers["ER"] = 68
names[68] = "Erbium"
colors[68] = (0, 230, 117)
radii[68] = 1.89

numbers["TM"] = 69
names[69] = "Thulium"
colors[69] = (0, 212, 82)
radii[69] = 1.90

numbers["YB"] = 70
names[70] = "Ytterbium"
colors[70] = (0, 191, 56)
radii[70] = 1.87

numbers["LU"] = 71
names[71] = "Lutetium"
colors[71] = (0, 171, 36)
radii[71] = 1.87

numbers["HF"] = 72
names[72] = "Hafnium"
colors[72] = (77, 194, 255)
radii[72] = 1.75

numbers["TA"] = 73
names[73] = "Tantalum"
colors[73] = (77, 166, 255)
radii[73] = 1.70

numbers["W"] = 74
names[74] = "Tungsten"
colors[74] = (33, 148, 214)
radii[74] = 1.62

numbers["RE"] = 75
names[75] = "Rhenium"
colors[75] = (38, 125, 171)
radii[75] = 1.51

numbers["OS"] = 76
names[76] = "Osmium"
colors[76] = (38, 102, 150)
radii[76] = 1.44

numbers["IR"] = 77
names[77] = "Iridium"
colors[77] = (23, 84, 135)
radii[77] = 1.41

numbers["PT"] = 78
names[78] = "Platinum"
colors[78] = (208, 208, 224)
radii[78] = 1.36

numbers["AU"] = 79
names[79] = "Gold"
colors[79] = (255, 209, 35)
radii[79] = 1.36

numbers["HG"] = 80
names[80] = "Mercury"
colors[80] = (184, 184, 208)
radii[80] = 1.32

numbers["TL"] = 81
names[81] = "Thallium"
colors[81] = (166, 84, 77)
radii[81] = 1.45

numbers["PB"] = 82
names[82] = "Lead"
colors[82] = (87, 89, 97)
radii[82] = 1.46

numbers["BI"] = 83
names[83] = "Bismuth"
colors[83] = (158, 79, 181)
radii[83] = 1.48

numbers["PO"] = 84
names[84] = "Polonium"
colors[84] = (171, 92, 0)
radii[84] = 1.40

numbers["AT"] = 85
names[85] = "Astatine"
colors[85] = (117, 79, 69)
radii[85] = 1.50

numbers["RN"] = 86
names[86] = "Radon"
colors[86] = (66, 130, 150)
radii[86] = 1.50

numbers["FR"] = 87
names[87] = "Francium"
colors[87] = (66, 0, 102)
radii[87] = 2.60

numbers["RA"] = 88
names[88] = "Radium"
colors[88] = (0, 125, 0)
radii[88] = 2.21

numbers["AC"] = 89
names[89] = "Actinium"
colors[89] = (112, 171, 250)
radii[89] = 2.15

numbers["TH"] = 90
names[90] = "Thorium"
colors[90] = (0, 186, 255)
radii[90] = 2.06

numbers["PA"] = 91
names[91] = "Protactinium"
colors[91] = (0, 161, 255)
radii[91] = 2.00

numbers["U"] = 92
names[92] = "Uranium"
colors[92] = (0, 143, 255)
radii[92] = 1.96

numbers["NP"] = 93
names[93] = "Neptunium"
colors[93] = (0, 128, 255)
radii[93] = 1.90

numbers["PU"] = 94
names[94] = "Plutonium"
colors[94] = (0, 107, 255)
radii[94] = 1.87

numbers["AM"] = 95
names[95] = "Americium"
colors[95] = (84, 92, 242)
radii[95] = 1.80

numbers["CM"] = 96
names[96] = "Curium"
colors[96] = (120, 92, 227)
radii[96] = 1.69

numbers["BK"] = 97
names[97] = "Berkelium"
colors[97] = (138, 79, 227)
radii[97] = 1.60

numbers["CF"] = 98
names[98] = "Californium"
colors[98] = (161, 54, 212)
radii[98] = 1.60

numbers["ES"] = 99
names[99] = "Einsteinium"
colors[99] = (179, 31, 212)
radii[99] = 1.60
numbers["FM"] = 100
names[100] = "Fermium"
colors[100] = (179, 31, 186)
radii[100] = 1.60

numbers["MD"] = 101
names[101] = "Mendelevium"
colors[101] = (179, 13, 166)
radii[101] = 1.60

numbers["NO"] = 102
names[102] = "Nobelium"
colors[102] = (189, 13, 135)
radii[102] = 1.60

numbers["LR"] = 103
names[103] = "Lawrencium"
colors[103] = (199, 0, 102)
radii[103] = 1.60

numbers["RF"] = 104
names[104] = "Rutherfordium"
colors[104] = (204, 0, 89)
radii[104] = 1.60

numbers["DB"] = 105
names[105] = "Dubnium"
colors[105] = (209, 0, 79)
radii[105] = 1.60

numbers["SG"] = 106
names[106] = "Seaborgium"
colors[106] = (217, 0, 69)
radii[106] = 1.60

numbers["BH"] = 107
names[107] = "Bohrium"
colors[107] = (224, 0, 56)
radii[107] = 1.60

numbers["HS"] = 108
names[108] = "Hassium"
colors[108] = (230, 0, 46)
radii[108] = 1.60

numbers["MT"] = 109
names[109] = "Meitnerium"
colors[109] = (235, 0, 38)
radii[109] = 1.60

numbers["DS"] = 110
names[110] = "Darmstadtium"
colors[110] = (255, 0, 255)
radii[110] = 1.60

numbers["RG"] = 111
names[111] = "Roentgenium"
colors[111] = (255, 0, 255)
radii[111] = 1.60

numbers["CN"] = 112
numbers["UUB"] = 112
names[112] = "Copernicium"
colors[112] = (255, 0, 255)
radii[112] = 1.60

numbers["UUT"] = 113
names[113] = "Ununtrium"
colors[113] = (255, 0, 255)
radii[113] = 1.60

numbers["UUQ"] = 114
names[114] = "Ununquadium"
colors[114] = (255, 0, 255)
radii[114] = 1.60

numbers["UUP"] = 115
names[115] = "Ununpentium"
colors[115] = (255, 0, 255)
radii[115] = 1.60

numbers["UUH"] = 116
names[116] = "Ununhexium"
colors[116] = (255, 0, 255)
radii[116] = 1.60

numbers["UUS"] = 117
names[117] = "Ununseptium"
colors[117] = (255, 0, 255)
radii[117] = 1.60

numbers["UUO"] = 118
names[118] = "Ununoctium"
colors[118] = (255, 0, 255)
radii[118] = 1.60

numbers["CV"] = 119
names[119] = "Cavity center"
colors[119] = (0, 0, 0)
radii[119] = 1.60

symbols = [None] * 120
for symbol, num in numbers.items():
    symbols[num] = symbol
