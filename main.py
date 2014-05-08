from __future__ import print_function

import datetime
import pickle

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import *
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.uix.gridlayout import GridLayout
from kivy.base import runTouchApp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import Screen
from kivy.uix.settings import SettingsWithSidebar
from kivy.uix.boxlayout import BoxLayout

from Deck import Deck

from jsonConfig import settingsjson

from gameplay import GamePlayScreen
game = None


'''initialize the score of players to 0'''

class SelectPlayersPopup(Popup):

    '''controls the values shown in the player selection popup'''

    def __init__(self, **kwards):
        super(SelectPlayersPopup, self).__init__()
        # More UI that I can't quite put in the kv file
        self.content = GridLayout(cols=2, spacing='10dp')
        self.buttons = [None] * number_of_players
        for i in range(number_of_players):
            self.buttons[i] = Button()
            self.buttons[i].text = game.name_of_players[i]
            self.buttons[i].value = i
            self.buttons[i].bind(on_press=self.click)
            self.content.add_widget(self.buttons[i])

    def click(self,button):
        self.update_scores(button.value)
        self.dismiss()

    def get_players_name(self, value):
        return name_of_players[value]

    def update_scores(self, value):
        '''need to other lines to update the score display'''
        print(value)
        game.scores_of_players[int(value)] += 1

class PlayerNamePopup(Popup):

    def __init__(self, value):
        super(PlayerNamePopup, self).__init__()
        self.text_inputs = [0]*value
        self.number_of_players = value
        game.number_of_players = value
        game.name_of_players = ['John', 'Sally', 'Sam', 'Joey']

        #Create the screen which allows a user to change names.
        self.content = GridLayout(cols=2, spacing='10dp')
        self.buttons = [None] * number_of_players
        for i in range(number_of_players):
            self.buttons[i] = Button()
            self.buttons[i].text = game.name_of_players[i]
            self.buttons[i].value = i
            self.buttons[i].bind(on_press=self.click)
            self.content.add_widget(self.buttons[i])
            
        self.enter = Button(text='Start Game', size_hint_y=None, height='40dp')

        self.enter.bind(on_press=self.on_press_callback)
        self.children[0].add_widget(self.enter)

    def click(self,button):
        #In here, we create the popup where we request the user's names.
        #On click of the name we want to change, the user can enter a new name.
        i = button.value
        popup = Popup(title="Enter text here",
              size_hint=(0.25, 0.25),
              on_dismiss=lambda x: self.set_caption(x,i,button))
        box = GridLayout(cols=1)
        box.add_widget(TextInput(focus=True,text=button.text))
        box.children[0].select_all()
        box.add_widget(Button(text="Enter Name",on_press = popup.dismiss) )
        popup.content = box
        popup.open()


    def set_caption(self, popup,i,button):
        #Set the name in the name_of_players array.
        game.name_of_players[i] = popup.content.children[1].text
        button.text = game.name_of_players[i]
        

    def on_press_callback(self, obj):
        self.dismiss()
        game.children[0].current = 'screen2'


class TutorialScreen(Screen):
    active = BooleanProperty(False)
    pass

class EndGameScreen(Screen):
    name_of_players = ListProperty(['','','',''])
    scores_of_players = ListProperty([0, 0, 0, 0])
    screenManager = ObjectProperty()
    number_of_players = NumericProperty(1)

    def on_enter(self,*args):
        print('gameover')
        self.name_of_players = [x for y,x in sorted(zip(game.scores_of_players,game.name_of_players))][::-1]
        self.scores_of_players = sorted(game.scores_of_players)[::-1]

class PlayerSection(Button):
    myvalue = NumericProperty(4)

    def __init__(self, **kwargs):
        super(PlayerSection, self).__init__(**kwargs)
        self.size = Window.size[0] // 6, Window.size[1] // 6


global current_angle
current_angle = 0



class CardToggle(ToggleButton):
    card = ObjectProperty()
    angle = NumericProperty(0)

class GameLayout(FloatLayout):
    score = NumericProperty(0)
    number_of_players = NumericProperty(1)
    score_display = StringProperty('')
    playersScores = ListProperty([0,0,0,0])
    soundActivated = BooleanProperty(False)

    hintActivated = BooleanProperty(False)
    
    # A variable that keeps tracked when an AI has played or not
    
    aiActivated = BooleanProperty(False)
    aiScore = NumericProperty(0)

    deck = ObjectProperty()
    cards = ListProperty([])

    name_of_players = ListProperty(['Collections found', '', '', ''])
    number_of_players = NumericProperty(1)
    scores_of_players = ListProperty([0, 0, 0, 0])

    # True if there is a game going on
    active = BooleanProperty(False)
    def __init__(self, **kwargs):
        super(GameLayout, self).__init__(**kwargs)
        global game
        game = self

        self.screens = self.ids.screenManager
        self.playscreen = self.screens.get_screen('screen2')
        # The UI element we were not able to add to collections.kv
        self.createGrid()
        self.sound = SoundLoader.load('set_song.wav')
        
        self.t0 = datetime.datetime.now()
    # screen play navigation
    def goToIntro(self, *arg):
        self.screens.current = 'screen1'

    def goToGameScreen(self):
        self.screens.current = 'screen2'

    def createGrid(self):
        ''' Create the grid of the 12 card buttons, should only be called once'''
        
        self.buttons = self.playscreen.ids.cards_layout.children
        # couldn't pass this on_press to the kv file.. no idea why

    def updateGrid(self):
        '''Updates the cards being displayed and updates hints/ai/numberofsets'''
        self.playscreen.updateGrid()
        self.t0 = datetime.datetime.now()
        if self.aiActivated:
            self.setUpAI()

    # Dealing with Sound
    def on_soundActivated(self, obj, value):
        ''' Turn the intro song on or off '''
        if value:
            self.sound.loop = True
            self.sound.play()
        else:
            self.sound.stop()

    # Functions related to the AIhint ###
    def setUpAI(self):
        Clock.unschedule(self.AIplay)
        if self.aiActivated and self.screens.current == 'screen2':
            (time, self.aiCards) = self.ai.suggestion(self.cards)
            Clock.schedule_once(self.AIplay, 1)

    def AIplay(self, *arg):
        ''' The AI plays a turn '''
        for index, card in enumerate(self.cards):
            if card in self.aiCards:
                self.buttons[index].state = 'down'
            else:
                self.buttons[index].state = 'normal'
        # Basic AI animation.
        Clock.schedule_once(lambda x: self.checkIfSetOnBoard(None), 1)
        self.aiPlayed = True

    def aiUpdates(self):
        timeDifference = datetime.datetime.now() - self.t0
        if self.aiActivated:
            if self.aiPlayed:
                self.ai.updateRatingsAI(
                    self.cards, self.aiCards, timeDifference)
            else:
                self.ai.updateRatingsHuman(
                    self.cards, selectedcards, timeDifference)

    # Functions related to displaying hint ###
    def on_displayHintTimer(self, obj, value):
        if self.screens.current == 'screen2':
            self.playscreen.setUpHint()

    # Functions to handling the game play screen
    def selected(self):
        '''Returns the indices of all the selected ToggleButton'''
        down = []
        for index, button in enumerate(self.buttons):
            if button.state == 'down':
                down.append(index)
        return down


    def unselectAll(self):
        ''' Unselect all the toggle buttons '''
        for button in self.buttons:
            button.state = 'normal'



    def rotateCards(self, cards):
        ''' selects the given cards if they are in the given cards '''
        for index, button in enumerate(self.buttons):
            if self.cards[index] in cards:
                button.rotate()




    # Dealing with multiplayer ###
    def select_player_popup(self, *args):
        '''called when three cards are selected'''
        popup = SelectPlayersPopup()
        popup.open()

    def set_players(self, value):
        '''set the number of players according to user's choice on the front page'''
        global number_of_players
        number_of_players = value

    def player_name_popup(self, numPlayers):
        '''called after selecting number of players'''
        playername = PlayerNamePopup(numPlayers)
        playername.open()

    def restart(self):
        '''reset the scores and everything'''
        global player_scores
        self.score_display = ''
        self.score = 0
        self.scores_of_players = [0,0,0,0]
        self.aiScore = 0

    def quit(self):
        ''' You are quiting the current game '''
        self.unselectAll()
        self.setupGame()
        self.restart()
        self.goToIntro()
        self.playscreen.stopRotation()
        self.active = False

    def goToTutorial(self):
        self.screens.current = 'tutorialFlow'

    def stopClocks(self):
        Clock.unschedule(self.AIplay)
        Clock.unschedule(self.playscreen.displayHint)
        Clock.unschedule(self.playscreen.displayHintSecond)

def boolFromJS(value):
    ''' JSON config returns '1' and '0' for True and False'''
    return True if value == '1' else False


class CollectionApp(App):
    active = BooleanProperty(False)

    def build(self):
        Clock.max_iteration = 50
        # The following line will be uncommented in the beta
        # For now, it gives us access to various kivy settings we can play with
        self.use_kivy_settings = False
        self.gamelayout = GameLayout()
        self.settings_cls = SettingsWithSidebar
        self.loadSettings()
        self.gamelayout.bind(active=self.changeActive)
        return self.gamelayout

    def changeActive(self,instance,value):
        # This doesn't work.. crashes if the build_settings wasn't launched first
        #self.quitButton.disabled = not self.gamelayout.active
        pass


    def loadSettings(self):
        # Load the values already stored into the file
        self.gamelayout.hintActivated = boolFromJS(
            self.config.get('settings', 'hint'))
        speedSettings = {'slow':10, 'normal':5, 'fast':1}
        self.gamelayout.displayHintTimer = speedSettings[
            self.config.get('settings', 'hintspeed')]
        self.gamelayout.soundActivated = boolFromJS(
            self.config.get('settings', 'sound'))
        self.gamelayout.aiActivated = boolFromJS(
            self.config.get('settings', 'ai'))

    def build_config(self, config):
        config.setdefaults('settings', {'hint': True, 
                                        'sound': False,
                                        'ai': False, 
                                        'hintspeed': 'fast'})

    def build_settings(self, settings):
        print(settings)
        self.settings = settings
        settings.add_json_panel('Settings', self.config, data=settingsjson)
        settingsCloseButton = settings.interface.ids.menu.ids.button
        self.settingsCloseButton = settingsCloseButton
        settingsCloseButton.on_press = self.leaveSettingsPanel
        settings.interface.ids.menu.add_widget(Button(text="Tutorial",
                                                      size_hint = (None, None),
                                                      x= settingsCloseButton.x,
                                                      y = settingsCloseButton.top + 10,
                                                      size = settingsCloseButton.size, 
                                                      on_press= self.moveToTutorial))

        self.quitButton = Button(text="Quit Current Game",
                              background_color = [1,0,0,1],
                              size_hint = (None, None),
                              x= settingsCloseButton.x,
                              y = settingsCloseButton.top + settingsCloseButton.height + 20,
                              size = settingsCloseButton.size,
                              disabled = False,
                              on_press= self.quit)   

        settings.interface.ids.menu.add_widget(self.quitButton)
        settings.on_close = self.quit

    def quit(self, *arg):
        self.gamelayout.quit()
        self.settingsCloseButton.trigger_action()

    def moveToTutorial(self, buttonInstance):
        self.gamelayout.goToTutorial()
        self.settingsCloseButton.trigger_action()

    def leaveSettingsPanel(self, *arg):       
        ''' activated when you exit the setting panels'''
        self.gamelayout.playscreen.setUpHint()
        self.gamelayout.playscreen.setUpAI()

    def on_config_change(self, config, section, key, value):
        if key == 'hint':
            self.gamelayout.hintActivated = boolFromJS(value)
        if key == 'sound':
            self.gamelayout.soundActivated = boolFromJS(value)
        if key == 'hintspeed':
            speedSettings = {'slow':10, 'normal':5, 'fast':1}
            self.gamelayout.displayHintTimer = speedSettings[value]
        if key == 'ai':
            self.gamelayout.aiActivated = boolFromJS(value)

# To test the screen size you can use:
# kivy main.py -m screen:ipad3

if __name__ == '__main__':
    CollectionApp().run()
