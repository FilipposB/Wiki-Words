import wikipedia
import re
import unicodedata as ud
import homoglyphs as hg
import random
import pygame
import csv
from difflib import SequenceMatcher

default_language="en"

#Set the language of the article
def init(language=default_language):
    default_language = language
    wikipedia.set_lang(language)

def load_language_data(language=default_language):
    frequency_table = dict()
    try:
        with open('freq_'+language+'.tsv') as tsv:
            for line in csv.reader(tsv, delimiter='\t'):
                if len(line) == 2:
                    frequency_table[line[0]] = int(line[1])
    except:
        with open('freq_'+language+'.tsv', 'w') as tsv:
            pass
    return frequency_table

def save_language_data(frequency_table, language=default_language):
    with open('freq_'+language+'.tsv', 'w', newline='') as tsv:
        writer = csv.writer(tsv, delimiter='\t')
        for key in frequency_table.keys():
            writer.writerow([key, frequency_table[key]])


def listToString(s): 
    # initialize an empty string
    str1 = "" 
    
    # traverse in the string  
    for ele in s: 
        str1 += ele  
    
    # return string  
    return str1

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def grab_word(game_board, start, finish):
    x_inc = finish[0] - start[0]
    if x_inc != 0:
        x_inc = 1
    y_inc = finish[1] - start[1]
    if y_inc != 0:
        y_inc = int(y_inc/abs(y_inc))
    pos = start
    result = ''
    while pos != finish:
        try:
            result += game_board[pos[1]][pos[0]]
        except:
            return result
        pos = (pos[0]+x_inc, pos[1]+y_inc)
    result += game_board[pos[1]][pos[0]]

    return result

#Returns if it fits and also the altered gam_board
def fits(game_board, word, x_start, y_start, width, height, x_inc, y_inc):
    tmp_board = game_board.copy()
    x, y = x_start, y_start
    for letter in word:
        if not (0 <= x < width) or not (0 <= y < height):
            return False, game_board
        if tmp_board[y][x]  == letter or game_board[y][x] ==' ':
            pass
        else:
            return False, game_board
        x, y = x+x_inc, y+y_inc
    x, y = x_start, y_start
    for letter in word:
        game_board[y][x] = letter
        x, y = x+x_inc, y+y_inc
    return True, game_board

def grab_words(source='',frequency_table=None, language=default_language):
    if source=='':
        article_name = wikipedia.random(pages=1)
    else:
        article_name = wikipedia.search(source, pages=1)
    try:
        article = wikipedia.page(article_name).content
    except wikipedia.DisambiguationError as e:
        article = wikipedia.page(random.choice(e.options))

    #Process the article
    d = {ord('\N{COMBINING ACUTE ACCENT}'):None}
    article = ud.normalize('NFD',article).upper().translate(d)
    #Remove all numbers
    article = re.sub("\d", "", article)
    #Extract all words
    words = re.findall(r'(\w+)', article, re.UNICODE)

    #Remove duplicates
    words = list(set(words))

    words = [s.strip() for s in words]

    if frequency_table == None:
        frequency_table = load_language_data(language=language)
    
    #Gather data
    for word in words:
        try:
            if word in frequency_table.keys():
                frequency_table[word] += 1
            else:
                frequency_table[word] = 1
        except:
            pass

    return article_name, words, frequency_table

#Gets a random page and extracts a few unique words
def produce_random_board(width=20, height=20, min_word_len=5, total_words=12, language=default_language):
    alphabet = listToString(hg.Languages.get_alphabet([language]))
    d = {ord('\N{COMBINING ACUTE ACCENT}'):None}
    alphabet = ud.normalize('NFD',alphabet).upper().translate(d)
    alphabet = re.sub(r"[^\w']+", "", alphabet, flags=re.UNICODE)
    alphabet = set(list(alphabet))
    alphabet = list(alphabet)
    
    while True:
        article_name, words, frequency_table = grab_words(language=language)
        try:    
            save_language_data(frequency_table, language=language)
        except:
            pass
        #Remove any words that don't match the language or are less than 4 letters
        for word in list(words):
            #Check if word belongs in the language
            belongs_in_language = True
            for letter in word:
                if not letter in alphabet:
                    belongs_in_language = False
                    break
            #print(word, len(word))
            #Check if the word is at least min_word_len letters or doesn't belogn in language
            if len(word) < min_word_len or not belongs_in_language:
                words.remove(word)

        #Check if the total amount of words is enough
        if len(words) >= total_words:
            break

    #Remove words that are too similar
    for word in list(words):
        for test_word in list(words):
            if 1 > similar(word, test_word) > 0.7:
                try:
                    words.remove(random.choice([word, test_word]))
                except:
                    pass
                break

    #Get the rarity of each word
    words_with_chances = dict.fromkeys(words)
    max_rarity = -1
    for word in words:
        try:
            words_with_chances[word]=frequency_table[word]
        except:
            words_with_chances[word]=0
        if words_with_chances[word]>max_rarity:
            max_rarity = words_with_chances[word]

    for key in words_with_chances:
        words_with_chances[key] = (max_rarity - words_with_chances[key] + 1)*10000

    #Sort the remaining words
    words_with_chances = dict(sorted(words_with_chances.items(), key=lambda item: item[1]))
    
    print(words_with_chances)
    words = list()
    #Keep total_words words
    while len(words) != total_words:
        print(words)
        words.extend(random.choices(list(set(list(words_with_chances.keys()))), weights=list(words_with_chances.values()), k=total_words-len(words)))
        words = list(set(words))
    
    #Create an empty board
    game_board = [[' ' for i in range(width)] for j in range(height)]

    #Place each word in the board
    for word in words:
        is_placed = False
        while not is_placed:            
            x = random.randint(0, width-1)
            y = random.randint(0, height-1)

            #0: Straight
            #1: Up-Straight
            #2: Down-Straight
            #3: Down
            x_inc, y_inc = 1, 0
            direction = random.randint(0, 3)
            if direction==1:
                x_inc, y_inc = 1, -1
            elif direction==2:
                x_inc, y_inc = 1, 1
            elif direction==3:
                x_inc, y_inc = 0, 1

            tmp_board = game_board.copy()
            is_placed, game_board = fits(tmp_board, word, x, y, width, height, x_inc, y_inc)

            
    print(article_name, words)

    #Fill the rest with random letters
    for y in range(0, height):
        for x in range(0, width):
            if game_board[y][x] == ' ':
                game_board[y][x]=random.choice(alphabet)

    print('\n\n')

    return article_name, words, game_board
    
#Main function
def main():
    init()
    pygame.init()
    # Set up the drawing window
    screen = pygame.display.set_mode([600, 700])
    white = (255, 255, 255)
    black = (0, 0, 0)
    green = (0, 128, 0)
    blue = (0, 0, 128)
    red = (128, 0, 0)

    # set the pygame window name
    pygame.display.set_caption('WikiScrummble')
    
    font = pygame.font.Font('freesansbold.ttf', 32)
    small_font = pygame.font.Font('freesansbold.ttf', 14)

    running = True

    while running:
        article_name, words, game_board = produce_random_board()

        textRect = pygame.Rect(0, 0, 30, 30)
        
        # Run until the user asks to quit
        prev_state = False
        starting_pos = (-1, -1)
        finishing_pos =(-1, -1)
        lines_to_draw = list()
        words_found=[False]*len(words)
        while False in words_found and running:

            # Did the user click the window close button?
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            #Logic
            pressed = pygame.mouse.get_pressed()[ 0 ]
            position = pygame.mouse.get_pos()

            # button pressed
            if pressed:
                if not prev_state:
                    prev_state = True
                    if (0 <= position[0] < 600 and 0 <= position[1] < 600):
                        starting_pos = position
            else:
                if prev_state:
                    if (0 <= position[0] < 600 and 0 <= position[1] < 600):
                        finishing_pos = position
                        pos1, pos2 = starting_pos, finishing_pos
                        pos1 = (int(pos1[0]/30), int(pos1[1]/30))
                        pos2 = (int(pos2[0]/30), int(pos2[1]/30))
                        if pos1[0] > pos2[0] or (pos1[0] == pos2[0] and pos2[1] < pos1[1]):
                            pos1, pos2 = pos2, pos1
                        res_word = grab_word(game_board, pos1, pos2)
                        print(res_word)
                        if res_word in words:
                            words_found[words.index(res_word)] = True
                            lines_to_draw.append(((pos1[0]*30+15, pos1[1]*30+15), (pos2[0]*30+15, pos2[1]*30+15)))
                    starting_pos = (-1, -1)
                prev_state = False

            #Draw

            # Fill the background with white
            screen.fill((255, 242, 204))
            x, y = textRect.width/2, textRect.height/2
            for line in game_board:
                for letter in line:
                    text = font.render(letter, True, black)
                    x_offset = 0
                    if letter == 'Ι' or letter=='I':
                        x_offset+=8
                    textRect.center = (x+x_offset, y)
                    screen.blit(text, textRect)
                    x += textRect.width
                x = textRect.width/2
                y += textRect.height

            textRect = pygame.Rect(0, 0, 30, 30)

            x, y = 5, 610
            text = small_font.render(article_name, True, green)
            small_textRect = text.get_rect()
            small_textRect.x = x
            small_textRect.y = y   
            screen.blit(text, small_textRect)

            y += small_textRect.height
            x_offset = 0
            max_word_len = 200
            for word in words:
                if words_found[words.index(word)]:
                     text = small_font.render(word, True, red)
                else:
                    text = small_font.render(word, True, blue)

                small_textRect = text.get_rect()
                if max_word_len < small_textRect.width:
                    max_word_len = small_textRect.width
                if y > 690:
                    y = 610 + small_textRect.height
                    x_offset += max_word_len
                small_textRect.x = x + x_offset
                small_textRect.y = y     
                screen.blit(text, small_textRect)
                y += small_textRect.height
 
            for line in lines_to_draw:
                pygame.draw.line(screen, red, line[0], line[1], 5)
                
            if starting_pos != (-1, -1):
                pygame.draw.line(screen, green, starting_pos, position, 5)

            
            # Flip the display
            pygame.display.flip()

    # Done! Time to quit.
    pygame.quit()

if __name__=="__main__":
    main()
