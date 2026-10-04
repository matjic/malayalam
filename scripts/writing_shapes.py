"""Hand-authored centerlines, guide curves, and label positions.

Reference: Moag, PDF pp. 27–46. Coordinates are design units, not scan pixels.
Each S() is a numbered movement in the source, not necessarily a pen lift.
Shared components are transformed geometrically; no raster tracing or font
outlines are used. Unnumbered context strokes have no guide or label.
"""

from copy import deepcopy


def S(name, ink, guide, x, y):
    return {'name': name, 'path': ink, 'guide': guide, 'label': [x, y]}


def move(strokes, x=0, y=0, scale=1, context=False):
    result = deepcopy(strokes)
    for stroke in result:
        previous = stroke.get('transform', '')
        stroke['transform'] = f'translate({x} {y}) scale({scale}) {previous}'.strip()
        if context:
            stroke['guide'] = None
            stroke['label'] = None
    return result


SHAPES = {}
TABLES = {page: [] for page in range(27, 47)}


def add(key, symbol, page, width, strokes, caption=None, height=180):
    SHAPES[key] = {'symbol': symbol, 'page': page, 'width': width,
                   'height': height, 'strokes': strokes, 'caption': caption or symbol}
    TABLES[page].append(key)
    return strokes


# Common counterclockwise loop, and the two movements of the tall au mark.
LOOP = [S('loop', 'M40 95 C40 72 72 72 72 95 C72 118 40 118 40 95',
          'M46 89 C58 76 68 88 64 100 C60 110 47 105 47 99', 56, 96)]
AU_MARK = [
    S('first arch', 'M20 85 V52 C20 24 54 24 54 52 V85',
      'M28 78 V52 C28 34 46 34 46 52 V78', 37, 58),
    S('second arch and bowl', 'M54 52 C54 24 88 24 88 52 V110 C88 138 42 138 42 110',
      'M62 78 V52 C62 34 80 34 80 52 V108 C80 128 53 130 51 116', 72, 94),
]


# Word-initial vowels, pp. 27–29.
A = add('vowel-a', 'അ', 27, 230, [
    S('left arch', 'M40 125 C-8 100 1 32 64 32',
      'M25 127 C-22 90 -5 18 55 18', 0, 79),
    S('upper inner bowl', 'M64 32 C109 32 114 75 76 76',
      'M73 44 C101 47 102 66 84 67', 86, 55),
    S('lower inner bowl', 'M76 76 C120 79 109 133 74 125',
      'M84 87 C104 100 97 115 84 115', 93, 102),
    S('inner return', 'M74 125 C31 116 27 58 64 32',
      'M56 113 C32 85 36 60 49 46', 36, 89),
    S('middle arch and downstroke', 'M64 32 C87 5 142 20 142 54 V125',
      'M112 38 C129 44 131 63 131 116', 122, 82),
    S('right arch', 'M142 125 V54 C142 12 196 13 218 54',
      'M153 116 V60 C153 34 170 28 184 29', 159, 83),
    S('right loop down', 'M218 54 C235 81 233 125 211 125',
      'M219 69 C224 87 224 108 215 116', 222, 95),
    S('right loop return', 'M211 125 C178 125 179 59 218 54',
      'M201 113 C184 96 192 72 206 66', 190, 92),
])
AA = add('vowel-aa', 'ആ', 27, 300, A + [
    S('long-vowel extension', 'M218 54 C296 58 302 158 252 158 C237 158 224 152 218 145',
      'M252 58 C311 82 315 153 269 171', 299, 116),
])
U = [*LOOP,
    S('outer arch', 'M40 95 C12 5 147 8 135 85 C131 117 115 141 84 140',
      'M26 86 C13 -8 156 2 148 84 C146 113 130 143 106 151', 118, 18),
    S('baseline turn', 'M84 140 H46 C14 140 14 169 46 169 H151',
      'M32 138 C4 148 8 184 49 184', 15, 167),
]
I = add('vowel-i', 'ഇ', 27, 220, [*LOOP,
    S('left arch', 'M40 95 C17 16 120 6 120 59 V104',
      'M23 87 C10 8 83 -4 108 22', 64, 7),
    S('right arch', 'M120 104 V59 C120 9 181 7 181 57 V112',
      'M130 94 V58 C130 34 143 25 157 26', 141, 52),
    S('lower return', 'M181 112 C181 137 159 143 139 143 H50',
      'M170 120 C166 133 137 131 95 132', 139, 120),
    S('baseline turn', 'M50 143 C13 143 13 169 50 169 H190',
      'M32 141 C3 152 14 183 57 183', 13, 164),
], height=200)
add('vowel-ii', 'ഈ', 27, 325, I + move(AU_MARK, 204, 12, .85), height=200)
add('vowel-u', 'ഉ', 27, 180, U, height=200)
add('vowel-uu', 'ഊ', 27, 295, U + move(AU_MARK, 174, 12, .9), height=200)
add('vowel-r', 'ഋ', 28, 190, [
    S('left loop', 'M33 42 C33 10 77 10 77 42 C77 72 33 72 33 42',
      'M43 38 C47 25 65 29 65 43 C65 55 44 57 44 44', 54, 43),
    S('left descent', 'M33 42 V82 C33 103 49 111 71 111',
      'M45 78 C45 90 53 96 65 99', 44, 87),
    S('lower oval', 'M71 111 C145 111 161 159 113 169 C70 179 32 163 43 139 C52 121 80 111 112 111',
      'M124 119 C157 132 154 157 125 174', 153, 143),
    S('right ascent', 'M112 111 C144 111 157 98 157 76 V42',
      'M75 100 C127 102 143 99 145 79', 112, 98),
    S('right loop', 'M157 42 C157 10 113 10 113 42 C113 72 157 72 157 42',
      'M145 38 C138 25 123 30 125 44 C128 58 146 56 145 45', 136, 44),
], height=200)
E = add('vowel-e', 'എ', 28, 240, [
    S('left curl', 'M35 113 C-14 87 6 24 48 35 C78 42 82 88 63 111',
      'M15 111 C-21 64 5 13 52 22 C85 27 97 73 80 99', 56, 14),
    S('crossbar', 'M63 111 H166', 'M71 125 H155', 116, 136),
    S('central ascent', 'M166 111 V40', 'M155 101 V48', 144, 75),
    S('central descent and turn', 'M166 40 V143 C166 192 108 166 108 115',
      'M178 48 V142', 189, 97),
    S('large arch', 'M108 115 C99 48 119 16 156 17 C192 17 216 52 218 103',
      'M98 111 C94 38 117 4 153 4', 108, 25),
    S('right descent', 'M218 103 C220 135 213 157 205 174',
      'M221 30 C245 68 245 135 221 174', 242, 101),
], height=205)
EE = add('vowel-ee', 'ഏ', 28, 240, E[:-1] + [
    S('upper right bowl', 'M218 103 C218 123 208 128 199 128',
      'M223 30 C251 70 244 114 219 125', 241, 86),
    S('lower right bowl', 'M199 128 C228 130 233 157 211 174',
      'M219 135 C242 148 242 166 226 182', 247, 157),
], height=205)
PRE_E = [*LOOP,
    S('outer arch', 'M40 95 C17 12 149 14 133 95 C130 112 118 125 107 131',
      'M23 87 C8 0 160 1 147 89 C145 107 133 127 121 137', 136, 23),
]
add('vowel-ai', 'ഐ', 28, 390, PRE_E + move(E, 150), height=205)
O = add('vowel-o', 'ഒ', 28, 170, [*LOOP,
    S('upper arch and bowl', 'M40 95 C15 15 140 11 139 64 C139 78 128 81 111 81',
      'M24 87 C6 0 156 0 151 62 C151 74 146 81 138 87', 105, 14),
    S('lower bowl', 'M111 81 C154 81 157 137 114 137 H111',
      'M143 92 C166 119 151 149 121 149', 164, 119),
])
AA_MARK = [S('long-a bowl', 'M33 40 C74 -5 119 104 63 128 C42 137 29 126 25 114',
             'M39 45 C72 21 103 98 66 117 C49 127 40 119 36 114', 93, 82)]
add('vowel-oo', 'ഓ', 28, 295, O + move(AA_MARK, 160))
add('vowel-au', 'ഔ', 29, 300, O + move(AU_MARK, 172, 8, 1.1))
DOT = [S('anusvara circle', 'M32 75 C32 42 76 42 76 75 C76 108 32 108 32 75',
         'M44 64 C62 50 74 76 57 87 C46 94 42 82 43 77', 55, 75)]
COLON = move(DOT, 0, -25, .75) + move(DOT, 0, 55, .75)
add('vowel-am', 'അം', 29, 335, A + move(DOT, 253, 31))
add('vowel-ah', 'അഃ', 29, 335, A + move(COLON, 256, 10))


# Dependent vowel signs, pp. 30–34. The gap is intentional: the base consonant
# belongs between the components of o/oo. HTML examples supply the base letters.
add('sign-aa', 'ാ', 30, 130, AA_MARK)
SIGN_I = add('sign-i', 'ി', 30, 110, [
    S('hook and descent', 'M25 35 C25 7 78 6 78 39 V147',
      'M37 36 C37 21 66 22 66 39 V140', 58, 60),
])
SIGN_II = add('sign-ii', 'ീ', 30, 110, move(LOOP, 2, -31, .75) + [
    S('arch and descent', 'M32 41 C20 6 84 2 84 40 V147',
      'M35 9 C65 -11 97 6 97 40 V144', 110, 83),
])
SIGN_U = add('sign-u', 'ു', 31, 110, [
    S('curved descent', 'M32 25 C98 -5 65 70 65 118',
      'M40 12 C109 -8 79 77 78 108', 99, 69),
    S('lower loop left', 'M65 118 C29 118 34 162 65 162',
      'M43 117 C20 135 23 172 54 175', 20, 145),
    S('lower loop right', 'M65 162 C99 162 97 118 65 118',
      'M77 175 C109 157 108 135 94 118', 111, 146),
], height=200)
add('sign-uu', 'ൂ', 31, 120, SIGN_U + move(LOOP, 29, 81, .53), height=200)
add('sign-r', 'ൃ', 31, 110, [
    S('curved descent', 'M76 20 C40 18 67 72 74 123',
      'M84 28 C54 27 81 75 86 125', 101, 88),
    S('lower loop', 'M74 123 C63 91 17 110 34 142 C50 170 81 150 74 123',
      'M47 160 C9 157 11 103 46 103', 15, 130),
])
add('sign-e', 'െ', 32, 175, PRE_E)
PRE_EE = add('sign-ee', 'േ', 32, 140, [
    S('upper loop', 'M85 43 C110 43 109 15 85 15 C59 15 62 44 85 43',
      'M84 21 C94 19 100 35 89 36 C79 37 76 30 79 25', 91, 29),
    S('left arc', 'M85 15 C8 6 9 138 82 138',
      'M87 1 C-10 -3 -8 154 69 154', 4, 89),
    S('lower loop', 'M82 138 C118 138 109 98 87 104 C69 107 64 126 82 138',
      'M110 126 C126 100 87 84 73 111', 119, 94),
])
add('sign-ai', 'ൈ', 32, 320, PRE_E + move(PRE_E, 150))
add('sign-o', 'ൊ', 33, 325, PRE_E + move(AA_MARK, 190))
add('sign-oo', 'ോ', 33, 285, PRE_EE + move(AA_MARK, 150))
add('sign-au', 'ൗ', 33, 135, AU_MARK)
add('sign-am', 'ം', 34, 115, DOT)
add('sign-ah', 'ഃ', 34, 100, COLON)


# Consonants, pp. 35–41. Keep the older handwritten forms in the reference,
# including thin straight stems, rather than substituting modern font outlines.
KA = add('ka', 'ക', 35, 250, [
    S('top arch', 'M91 65 V42 C91 9 146 9 146 42 V65',
      'M80 57 V42 C80 -7 158 -7 158 42 V57', 143, 4),
    S('right bowl return', 'M146 65 V104 C146 139 91 139 91 104',
      'M158 80 V103 C158 152 92 154 84 128', 129, 149),
    S('middle ascent', 'M91 104 V65', 'M103 108 V76', 114, 93),
    S('left bowl return', 'M91 65 V104 C91 139 37 139 37 104',
      'M79 79 V103 C79 121 66 126 56 119', 68, 96),
    S('left arch', 'M37 104 C24 69 46 65 65 65',
      'M26 126 C1 102 7 55 47 53', 9, 97),
    S('crossbar', 'M65 65 H188', 'M71 53 H182', 175, 41),
    S('right end', 'M188 65 C226 65 232 101 211 124',
      'M215 53 C252 73 252 110 227 136', 249, 96),
])
KHA = add('kha', 'ഖ', 35, 250, PRE_E + [
    S('baseline', 'M107 131 H216', 'M113 145 H207', 162, 159),
    S('right ascent', 'M216 131 V21', 'M228 129 V27', 241, 80),
])
GA = add('ga', 'ഗ', 35, 235, [
    S('left bowl', 'M40 25 C-3 40 8 130 66 131 C106 132 113 105 113 78',
      'M42 38 C10 51 31 117 66 117', 28, 85),
    S('right arch', 'M113 78 V62 C113 5 205 8 209 75',
      'M101 89 V60 C101 -6 191 -8 206 36', 176, 5),
    S('right descent', 'M209 75 C211 100 197 122 176 135',
      'M225 67 C225 106 211 127 193 142', 235, 115),
])
GHA = add('gha', 'ഘ', 35, 305, E[:2] + [
    S('middle arch', 'M166 111 V49 C166 12 105 10 105 49 V111',
      'M179 101 V45 C179 -3 92 -2 92 45 V101', 136, 4),
    S('middle descent', 'M105 111 V154', 'M93 119 V150', 82, 138),
    S('baseline', 'M105 154 H273', 'M112 168 H267', 191, 180),
    S('right ascent', 'M273 154 V23', 'M285 150 V29', 300, 93),
], height=205)
NGA = add('nga', 'ങ', 35, 245, [*LOOP,
    S('left arch', 'M40 95 C12 12 127 3 127 52',
      'M22 84 C5 -1 89 -10 117 16', 79, 1),
    S('middle descent', 'M127 52 V134', 'M115 54 V126', 105, 95),
    S('upper right bowl', 'M127 134 V52 C127 11 217 4 217 54 C217 74 198 75 172 75',
      'M140 125 V52 C140 26 200 17 204 51 C205 61 199 62 188 63', 162, 47),
    S('lower right bowl', 'M172 75 C232 73 231 135 180 135 H172',
      'M185 87 C215 87 213 123 184 123', 204, 105),
])
CHA = add('cha', 'ച', 36, 250, [
    S('upper curl', 'M51 81 C17 64 32 16 66 23 C87 27 101 45 104 63',
      'M30 75 C12 42 29 8 66 9', 29, 25),
    S('curl and leftward baseline', 'M104 63 C110 101 77 129 23 129',
      'M92 57 C99 92 69 116 30 116', 58, 108),
    S('baseline', 'M23 129 H219', 'M28 143 H211', 114, 155),
    S('right ascent', 'M219 129 V18', 'M232 129 V26', 245, 80),
])
add('chha', 'ഛ', 36, 330, CHA[:3] + move([
    S('right arch', 'M35 113 C-14 87 1 15 56 15 C103 15 124 59 114 97',
      'M17 108 C-28 54 7 -4 58 2 C112 4 143 62 128 103', 136, 59),
    S('right loop', 'M114 97 C95 66 55 71 56 99 C57 132 113 135 114 97',
      'M105 103 C104 84 70 82 69 99 C68 116 98 120 101 108', 83, 101),
], 184, 16))
JA = add('ja', 'ജ', 36, 220, [*move(LOOP, 0, -52, .8),
    S('left arch', 'M32 24 C14 -6 101 -7 101 23 V53',
      'M20 26 C7 -18 72 -22 91 -4', 54, -16),
    S('right arch', 'M101 53 V23 C101 -6 171 -8 171 24 C171 36 163 41 142 47',
      'M113 46 V23 C113 4 155 6 158 21', 142, 9),
    S('diagonal return', 'M142 47 L44 82 C-1 97 34 124 61 111',
      'M148 59 L41 95 C17 106 26 126 46 126', 15, 106),
    S('lower diagonal', 'M61 111 L141 77 C155 70 174 72 174 89',
      'M58 99 L140 65 C151 59 167 58 178 62', 107, 76),
    S('right loop', 'M174 89 C174 112 142 112 142 89 C142 65 174 65 174 89',
      'M187 84 C199 119 140 138 128 103', 178, 123),
], height=180)
THA = [
    S('left arch', 'M41 131 C-5 105 1 26 60 26 C98 26 120 65 115 94',
      'M25 130 C-23 85 -3 13 55 13', 0, 72),
    S('central loop down', 'M115 94 C108 141 59 142 56 92',
      'M105 49 C127 94 109 130 86 143', 121, 115),
    S('central loop up and right arch', 'M56 92 C51 52 89 17 130 26 C184 35 191 101 158 130',
      'M45 119 C27 59 73 4 125 13', 76, 17),
    S('right descent', 'M158 130 C171 119 181 104 181 85',
      'M183 30 C217 75 203 111 179 138', 208, 94),
]
DDA = [
    S('left arch', 'M40 132 C-9 104 8 21 58 24 C84 25 97 43 97 74',
      'M24 132 C-25 83 0 12 53 11', 0, 72),
    S('left descent', 'M97 74 V106 C97 142 151 142 151 106',
      'M89 32 C114 39 108 83 108 99', 112, 67),
    S('middle ascent', 'M151 106 V24', 'M139 112 V32', 128, 73),
    S('right bowl', 'M151 24 V106 C151 142 205 142 213 112',
      'M164 33 V91 C164 109 176 120 188 121', 174, 100),
    S('right return', 'M213 112 C233 78 225 42 199 24',
      'M203 145 C251 126 250 62 226 34', 248, 95),
]
add('jha', 'ഝ', 36, 310, THA + move(DDA[2:], 30))
NYA = add('nya', 'ഞ', 36, 350, [*LOOP,
    S('left arch', 'M40 95 C13 17 116 6 119 52',
      'M23 87 C6 0 83 -6 106 14', 67, 2),
    S('middle descent', 'M119 52 V131', 'M108 54 V123', 98, 94),
    S('middle loop ascent', 'M119 131 V52 C119 1 229 17 229 79',
      'M133 119 V59 C133 34 160 28 174 35', 146, 71),
    S('middle loop return', 'M229 79 C229 137 174 143 169 98 C165 72 179 52 195 40',
      'M213 58 C241 113 200 147 187 115', 211, 104),
    S('right arch', 'M195 40 C230 -1 309 25 309 76',
      'M158 82 C161 17 251 -14 286 14', 244, 5),
    S('right descent', 'M309 76 C309 104 295 123 279 135',
      'M308 23 C345 67 332 116 299 144', 339, 94),
])
TTA = add('tta', 'ട', 37, 160, [
    S('upper curl', 'M131 43 C98 1 25 11 25 56 C25 76 48 80 76 80',
      'M119 17 C72 -7 19 7 13 45', 26, 3),
    S('lower curl', 'M76 80 C139 77 153 137 88 137 C57 137 36 130 27 115',
      'M31 94 C163 75 151 128 65 125', 90, 109),
])
add('ttha', 'ഠ', 37, 145, move(DOT, -19, -21, 1.9))
add('dda', 'ഡ', 37, 270, DDA)
add('ddha', 'ഢ', 37, 280, DDA[:-1] + [
    S('right loop ascent', 'M213 112 C241 89 241 26 211 24',
      'M183 123 C209 127 228 101 228 86', 219, 117),
    S('right loop', 'M211 24 C177 24 179 69 211 69 C237 69 241 24 211 24',
      'M221 35 C212 24 193 32 195 46 C196 57 215 60 218 52', 209, 44),
])
NNA = add('nna', 'ണ', 37, 310, [*LOOP,
    S('left arch', 'M40 95 C12 15 118 7 121 48',
      'M24 87 C4 0 89 -9 109 14', 67, 3),
    S('first stem', 'M121 48 V132', 'M110 51 V123', 99, 91),
    S('middle arch', 'M121 132 V48 C121 12 181 12 181 48',
      'M134 123 V52 C134 30 145 27 154 29', 142, 68),
    S('second stem', 'M181 48 V132', 'M169 51 V123', 159, 91),
    S('right arch', 'M181 132 V48 C181 9 249 12 271 59',
      'M194 123 V53 C194 30 209 25 222 29', 204, 68),
    S('right descent', 'M271 59 C286 93 272 116 249 133',
      'M235 15 C307 38 309 102 269 141', 303, 92),
])
add('tha', 'ത', 38, 240, THA)
add('thha', 'ഥ', 38, 260, [
    S('left descent', 'M28 23 V132', 'M15 29 V128', 4, 82),
    S('baseline', 'M28 132 H230', 'M35 147 H219', 128, 161),
    S('right arch', 'M230 132 V67 C230 9 121 9 121 67 V132',
      'M243 119 V66 C243 -7 108 -7 108 66 V116', 186, 8),
])
DA = add('da', 'ദ', 38, 180, [
    S('left arch', 'M45 131 C-9 102 0 20 71 21',
      'M27 136 C-34 94 -8 7 56 8', 0, 70),
    S('upper bowl', 'M71 21 C143 14 168 76 87 76',
      'M101 9 C171 33 163 69 135 79', 169, 48),
    S('lower bowl', 'M87 76 C165 71 167 132 87 132',
      'M135 89 C167 111 142 147 97 146', 169, 121),
])
DHA = add('dha', 'ധ', 38, 260, [
    S('left bowl', 'M50 24 C-6 43 9 138 75 132',
      'M32 27 C-23 63 -2 138 48 146', 0, 92),
    S('middle ascent', 'M75 132 C108 132 130 108 130 78 V24',
      'M55 120 C104 130 117 103 117 33', 101, 85),
    S('right bowl', 'M130 24 V78 C130 144 203 146 224 107',
      'M143 34 C143 116 157 117 172 122', 154, 101),
    S('right return', 'M224 107 C242 79 238 44 211 24',
      'M198 148 C269 126 270 63 239 32', 260, 99),
])
NA = add('na', 'ന', 38, 240, [
    S('left arch', 'M40 131 C-9 105 6 25 58 25 C89 25 105 47 105 73',
      'M22 133 C-30 86 -6 11 54 12', 0, 69),
    S('middle descent', 'M105 73 V130', 'M94 49 V120', 83, 89),
    S('right arch', 'M105 130 V73 C105 11 207 13 207 73',
      'M118 119 V74 C118 39 136 31 146 33', 135, 65),
    S('right descent', 'M207 73 C207 101 194 118 174 130',
      'M179 15 C237 44 237 108 197 139', 230, 82),
])
PA = add('pa', 'പ', 39, 260, [
    S('left curl', 'M43 130 C-10 100 16 41 54 46 C100 47 111 104 86 127',
      'M24 130 C-29 83 10 29 61 32 C104 36 123 79 109 106', 102, 52),
    S('baseline', 'M86 127 H222', 'M95 141 H213', 154, 155),
    S('right ascent', 'M222 127 V20', 'M235 125 V28', 248, 80),
])
add('pha', 'ഫ', 39, 295, PA[:2] + [
    S('right arch', 'M222 127 V63 C222 9 136 9 136 63 V127',
      'M235 115 V60 C235 -6 123 -6 123 60 V116', 190, 5),
])
BA = add('ba', 'ബ', 39, 300, [*LOOP,
    S('left arch', 'M40 95 C13 11 118 7 122 52',
      'M23 87 C4 -1 90 -10 110 17', 70, 2),
    S('middle descent', 'M122 52 V131', 'M110 56 V121', 99, 91),
    S('right arch', 'M122 131 V52 C122 -7 234 4 234 68',
      'M135 119 V58 C135 31 158 21 171 25', 147, 65),
    S('right descent', 'M234 68 C234 98 223 114 200 131',
      'M213 11 C265 41 265 98 246 121', 269, 74),
    S('baseline', 'M200 131 H279', 'M212 145 H270', 241, 156),
    S('right ascent', 'M279 131 V22', 'M292 128 V29', 304, 78),
])
add('bha', 'ഭ', 39, 175, [
    S('left arch', 'M46 133 C-10 103 -3 20 75 22',
      'M27 139 C-37 90 -6 5 61 9', 0, 73),
    S('top bowl', 'M75 22 C128 20 133 59 112 60',
      'M105 9 C154 32 148 57 136 67', 159, 43),
    S('middle curl', 'M112 60 H78 C40 60 42 91 78 91 H102',
      'M50 71 C30 100 46 113 72 104', 40, 95),
    S('lower bowl', 'M102 91 C145 91 140 133 108 133 H66',
      'M132 85 C165 122 147 149 99 148', 163, 122),
])
MA = add('ma', 'മ', 39, 185, [
    S('left arch', 'M31 134 V63 C31 34 46 25 79 25',
      'M18 125 V64 C18 25 40 11 67 11', 11, 64),
    S('right arch', 'M79 25 C128 25 152 35 152 70 V134',
      'M95 10 C152 10 167 33 167 70 V122', 170, 64),
    S('baseline', 'M152 134 H31', 'M140 149 H40', 86, 162),
    S('inner bowl', 'M53 134 C108 132 123 69 79 25',
      'M51 122 C96 118 99 70 84 47', 99, 88),
])
YA = add('ya', 'യ', 40, 270, [
    S('left bowl', 'M69 23 C-7 14 -14 129 73 132',
      'M48 9 C-34 30 -27 129 38 146', 0, 75),
    S('middle loop up', 'M73 132 C152 132 155 24 120 23',
      'M85 145 C152 122 165 67 153 26', 165, 72),
    S('middle loop down', 'M120 23 C75 21 48 118 143 132',
      'M104 9 C60 28 56 95 100 120', 76, 76),
    S('right bowl', 'M143 132 C243 147 259 69 214 22',
      'M181 146 C264 145 278 81 250 30', 272, 89),
])
RA = add('ra', 'ര', 40, 180, [
    S('left arch', 'M45 132 C-9 103 0 18 74 22 C105 23 124 40 131 65',
      'M26 136 C-37 85 -5 4 78 9', 0, 65),
    S('right loop descent', 'M131 65 C150 127 125 142 101 132',
      'M142 40 C174 88 161 129 144 143', 173, 103),
    S('right loop return', 'M101 132 C62 114 75 57 131 65',
      'M95 118 C68 86 89 61 111 56', 76, 90),
])
LA = add('la', 'ല', 40, 240, [
    S('crossbar', 'M31 78 H131', 'M45 93 H119', 82, 108),
    S('upper arch', 'M131 78 V47 C131 11 31 11 31 47 V78',
      'M144 73 V46 C144 -7 18 -7 18 46 V72', 74, 3),
    S('left descent', 'M31 78 V138', 'M18 88 V130', 4, 114),
    S('baseline', 'M31 138 H209', 'M39 153 H200', 123, 168),
    S('right ascent', 'M209 138 V24', 'M222 135 V31', 237, 84),
], height=195)
VA = add('va', 'വ', 40, 240, [
    S('left curl', 'M44 133 C-7 106 6 24 65 24 C107 24 139 85 104 131',
      'M25 134 C-32 85 -3 10 68 11 C127 12 150 92 129 114', 110, 14),
    S('baseline', 'M104 131 H210', 'M112 145 H200', 157, 160),
    S('right ascent', 'M210 131 V22', 'M223 128 V29', 237, 78),
])
add('sha', 'ശ', 40, 235, GA[:-1] + [
    S('right descent', 'M209 75 C211 112 193 135 173 135',
      'M216 30 C248 71 241 111 215 137', 241, 102),
    S('right loop', 'M173 135 C124 135 126 82 173 82 C215 82 212 135 173 135',
      'M162 123 C135 115 143 91 165 94', 169, 109),
])
add('ssa', 'ഷ', 40, 305, PA[:2] + [
    S('right ascent', 'M222 127 V10', 'M237 120 V17', 252, 67),
    S('diagonal return', 'M222 10 L123 69', 'M217 28 L124 84', 162, 61),
    S('upper loop', 'M123 69 C65 108 68 -29 120 16 C133 27 137 50 123 69',
      'M83 41 C50 4 97 -34 123 -3 C135 12 144 29 144 40', 107, -15),
    S('middle descent', 'M123 69 V127', 'M137 78 V119', 151, 105),
])
SA = add('sa', 'സ', 41, 300, NA[:3] + [
    S('right descent', 'M207 73 V98 C207 143 270 145 277 103',
      'M192 26 C224 24 221 65 221 96', 232, 74),
    S('right bowl return', 'M277 103 C290 75 282 44 257 23',
      'M239 147 C312 128 317 64 282 31', 309, 92),
])
add('ha', 'ഹ', 41, 300, PA[:2] + [
    S('right arch', 'M222 127 C155 108 171 5 231 16 C284 25 284 105 249 130',
      'M190 119 C131 40 200 -24 258 9 C307 39 307 111 269 140', 295, 55),
])
LLA = add('lla', 'ള', 41, 195, O[:2] + [
    S('lower bowl and return', 'M111 81 C159 82 169 141 108 153 H52',
      'M146 90 C187 126 159 163 92 164', 181, 127),
    S('baseline turn', 'M52 153 C13 153 13 185 52 185 H172',
      'M33 151 C0 157 5 200 64 200', 12, 180),
], height=220)
add('zha', 'ഴ', 41, 190, [
    S('left bowl', 'M40 25 C-8 50 7 99 75 99 H113',
      'M22 28 C-32 73 4 114 86 114', 0, 79),
    S('upper loop', 'M113 99 C152 92 149 23 102 23 C53 23 62 98 113 99',
      'M146 89 C185 7 54 -17 56 65', 94, 8),
    S('lower bowl', 'M113 99 C163 166 69 175 50 142',
      'M126 117 C167 166 89 200 57 161', 155, 166),
], height=210)
RRA = add('rra', 'റ', 41, 185, [
    S('open arch', 'M45 135 C-25 91 10 17 79 22 C139 26 156 98 109 135',
      'M24 139 C-50 67 14 -6 87 9 C168 24 180 97 136 141', 175, 86),
])


# Chillus, pp. 42–43: a loop plus rising tail, with separate final curl.
def tail(x, y, scale=1):
    return move([
        S('tail ascent', 'M0 0 C-24 -36 24 -62 24 -89',
          'M-10 -12 C-23 -42 29 -69 37 -90', 31, -64),
        S('tail curl', 'M24 -89 C24 -128 -25 -129 -25 -103',
          'M37 -104 C29 -155 -43 -143 -39 -112', 4, -151),
    ], x, y, scale)

add('chillu-nn', 'ൺ', 42, 320, NNA[:-1] + [
    S('right loop', 'M271 59 C303 123 245 170 249 133',
      'M280 64 C306 92 290 130 274 142', 312, 111),
] + tail(249, 133, .8), caption='ണ → ൺ', height=210)
add('chillu-n', 'ൻ', 42, 265, NA[:-1] + [
    S('right loop', 'M207 73 C232 125 176 156 174 130',
      'M220 80 C246 106 218 147 193 147', 251, 115),
] + tail(174, 130, .8), caption='ന → ൻ', height=210)
add('chillu-r', 'ർ', 42, 200, RA[:2] + [
    S('inner loop and tail ascent',
      'M101 132 C62 114 75 57 131 65 M101 132 C82 103 120 82 120 61',
      'M95 118 C68 86 89 61 111 56', 76, 90),
] + tail(101, 132, .8)[-1:], caption='ര → ർ', height=210)
add('chillu-l', 'ൽ', 43, 265, THA + tail(158, 130, .9), caption='ല → ൽ', height=220)
add('chillu-ll', 'ൾ', 43, 290, [
    S('left bowl', 'M50 82 C-6 109 14 160 69 159 C92 159 110 146 137 123',
      'M23 84 C-23 115 10 176 67 173', 0, 133),
    S('diagonal ascent', 'M137 123 L191 74 C221 43 264 57 264 97',
      'M101 137 L186 60 C211 30 249 33 263 51', 217, 33),
    S('right bowl', 'M264 97 C264 141 231 154 202 123 L126 46',
      'M278 75 C304 134 252 183 206 151', 284, 137),
    S('upper left curl', 'M126 46 L74 -1 C45 -29 24 15 43 23',
      'M152 56 L69 -21 C21 -60 -2 4 16 21', 77, -22),
], caption='ള → ൾ', height=210)
VIRAMA = [S('virama', 'M12 4 C22 31 48 31 58 4',
            'M20 0 C30 17 41 17 51 0', 34, 28)]
for key, base in [('ka', KA), ('cha', CHA), ('tta', TTA), ('tha', THA), ('pa', PA)]:
    add(f'bare-{key}', SHAPES[key]['symbol'] + '്', 43,
        SHAPES[key]['width'], move(base, context=True) + move(VIRAMA, SHAPES[key]['width'] - 80, -24, context=True),
        height=190)


# Doubled consonants, pp. 44–45. These are ligatures, not two adjacent letters.
add('double-ka', 'ക്ക', 44, 340, KA[:2] + [
    S('left bowl and arch', 'M91 65 V104 C91 139 37 139 37 104 C24 69 46 65 65 65',
      'M78 124 C8 166 0 67 47 53', 9, 97),
    KA[2],
    S('middle loop', 'M188 65 C257 48 254 154 202 128 C183 120 176 95 188 65',
      'M210 64 C241 96 229 140 207 143', 243, 119),
    S('right arch', 'M65 65 H188 C235 11 300 43 294 95 C293 110 288 119 278 128',
      'M200 43 C263 2 326 59 309 103 C306 117 302 126 294 135', 327, 89),
])
add('double-nga', 'ങ്ങ', 44, 345, NGA[:3] + [
    S('middle upper bowl', 'M127 52 C127 11 217 4 217 54 C217 74 198 75 172 75',
      'M140 48 C140 23 198 15 204 50 C205 61 199 62 188 63', 192, 37),
    S('middle lower bowl', 'M172 75 C224 75 232 135 179 135',
      'M184 87 C215 87 213 124 184 123', 205, 106),
    S('right arch and upper bowl', 'M217 54 C222 -5 307 11 307 54 C307 74 288 75 262 75',
      'M231 50 C228 25 287 15 294 48', 295, 16),
    S('right lower bowl', 'M262 75 C321 73 322 135 270 135 H262',
      'M302 88 C332 114 306 148 280 148', 335, 121),
])


def wedge(x=0, y=0):
    return move([
        S('right descent', 'M210 22 V181', 'M223 33 V173', 237, 107),
        S('lower baseline', 'M210 181 H98', 'M200 195 H107', 150, 207),
        S('diagonal return', 'M98 181 L210 145', 'M106 167 L196 137', 153, 142),
    ], x, y)


add('double-cha', 'ച്ച', 44, 265, CHA + wedge(9), height=230)
add('double-tha', 'ത്ത', 44, 390, THA[:3] + [
    S('first stem', 'M181 85 V131', 'M194 89 V124', 206, 112),
    S('second arch', 'M181 131 V85 C181 25 263 9 296 49',
      'M168 121 V88 C168 5 246 -3 267 11', 224, 3),
    S('second loop down', 'M296 49 C351 112 286 159 265 119',
      'M310 53 C348 98 330 137 312 146', 345, 103),
    S('second loop return', 'M265 119 C244 79 277 21 318 27',
      'M250 115 C224 58 275 1 309 11', 258, 50),
    S('right descent', 'M318 27 C374 43 383 96 353 132',
      'M335 13 C404 31 410 108 375 143', 401, 84),
])
add('double-tta', 'ട്ട', 44, 165, TTA + [
    S('additional lower bowl', 'M88 137 C160 128 156 191 88 191 C57 191 36 184 27 169',
      'M32 148 C161 131 151 182 66 179', 92, 163),
], height=225)
add('double-nna', 'ണ്ണ', 44, 490, NNA[:6] + [
    S('third stem', 'M271 59 V133', 'M258 61 V124', 247, 96),
    S('third arch', 'M271 133 V59 C271 9 380 12 380 78',
      'M285 122 V60 C285 34 308 29 322 30', 299, 66),
    S('third loop return', 'M380 78 C381 132 329 153 320 114',
      'M367 58 C395 99 373 143 351 153', 390, 108),
    S('third loop ascent', 'M320 114 C307 62 359 5 405 24',
      'M305 122 C280 54 346 -6 384 8', 323, 52),
    S('right descent', 'M405 24 C459 43 472 99 437 136',
      'M420 9 C490 32 500 108 460 147', 490, 81),
])
add('double-na', 'ന്ന', 44, 320, NA[:3] + [
    S('second stem', 'M207 73 V131', 'M194 76 V123', 183, 105),
    S('right arch', 'M207 131 V73 C207 10 292 17 292 73',
      'M220 121 V75 C220 44 238 31 251 33', 233, 68),
    S('right descent', 'M292 73 C293 100 281 119 260 131',
      'M265 18 C324 49 325 108 284 142', 323, 94),
])
add('double-ba', 'ബ്ബ', 44, 310, [
    S('left loop, arch, and stem',
      'M40 95 C40 72 72 72 72 95 C72 118 40 118 40 95 '
      'M40 95 C13 11 118 7 122 52 V131',
      'M23 87 C4 -1 90 -10 110 17', 70, 2),
    S('right arch', 'M122 131 V52 C122 -7 234 4 234 68 C234 98 223 114 200 131',
      'M135 119 V58 C135 31 158 21 171 25', 147, 65),
] + BA[5:] + wedge(69), height=230)
add('double-ma', 'മ്മ', 45, 315, MA + [
    S('second arch', 'M152 134 V63 C152 34 167 25 200 25 C249 25 273 35 273 70 V134',
      'M140 122 V64 C140 -7 285 -4 285 70 V122', 287, 61),
] + move(MA[2:], 121))
add('double-ya', 'യ്യ', 45, 280, YA + wedge(41), height=230)
SUB_LA = [
    S('lower loop', 'M40 95 C40 72 72 72 72 95 C72 118 40 118 40 95',
      'M46 89 C58 76 68 88 64 100 C60 110 47 105 47 99', 56, 96),
    S('lower stem', 'M40 95 C14 33 95 25 95 72 V100',
      'M32 57 C14 27 103 9 107 65 V87', 93, 28),
    S('lower bowl', 'M95 100 C95 154 178 161 176 79',
      'M107 112 C132 169 198 149 190 86', 173, 151),
]
add('double-la', 'ല്ല', 45, 250, LA + move([
    S('lower loop and arch',
      'M40 95 C40 72 72 72 72 95 C72 118 40 118 40 95 '
      'M40 95 C14 33 95 25 95 72 V100',
      'M32 57 C14 27 103 9 107 65 V87', 93, 28),
    SUB_LA[2],
], 27, 116, .9), height=285)
add('double-va', 'വ്വ', 45, 260, VA + wedge(), height=230)
add('double-pa', 'പ്പ', 45, 265, PA + move(PA[:2], 0, 69) + [
    S('second ascent', 'M222 196 V20', 'M249 188 V28', 262, 102),
], height=230)
add('double-lla', 'ള്ള', 45, 375, LLA[:-1] + [
    S('first baseline turn', 'M52 153 C13 153 13 185 52 185 H224',
      'M33 151 C0 157 5 200 64 200', 12, 180),
] + move(LLA, 172), height=230)


# Joining forms, p. 46: only the added sign is numbered in the reference.
JOIN_YA = [S('postposed ya', 'M31 21 C23 88 66 126 30 149 C7 165 -6 144 9 133',
             'M44 25 C32 89 87 125 44 165 C12 190 -29 151 -4 136', 71, 134)]
JOIN_RA = [S('preposed ra', 'M27 24 V146 C27 174 44 177 69 165',
             'M14 29 V149 C14 189 38 195 58 187', 0, 107)]
JOIN_VA = [
    S('joining baseline', 'M13 136 H70', 'M19 151 H62', 43, 165),
    S('joining ascent', 'M70 136 V25', 'M83 131 V33', 96, 81),
]
add('join-ya', 'ത്യ', 46, 310, move(THA, context=True) + move(JOIN_YA, 234),
    caption='ത് + യ = ത്യ', height=220)
add('join-ra', 'പ്ര', 46, 360, move(PA, 92, context=True) + JOIN_RA,
    caption='പ + ര / റ = പ്ര', height=210)
add('join-la', 'പ്ല', 46, 265, move(PA, context=True) + move(SUB_LA, 54, 101, .95),
    caption='പ + ല = പ്ല', height=285)
add('join-va', 'സ്വ', 46, 415, move(SA, context=True) + move(JOIN_VA, 314),
    caption='സ + വ = സ്വ', height=210)
