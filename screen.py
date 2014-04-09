from __future__ import print_function

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.properties import NumericProperty, ReferenceListProperty,\
    ObjectProperty
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.image import Image


class GameLayout(FloatLayout):

    def __init__(self, **kwargs):
        self.btns = [None] * 12
        super(GameLayout, self).__init__(**kwargs)
        playscreen = self.children[0].get_screen('screen2')
        for i in range(12):
            btn_text = 'Button' + str(i + 1)
            self.btns[i] = ToggleButton(text=btn_text)
            self.btns[i].bind(
                on_press=self.on_press_callback, state=self.state_callback)
            # print(self.btns[i].center)
            playscreen.children[0].add_widget(self.btns[i])

    def play(self):
        playscreen = self.children[0].get_screen('screen2')
        for i in range(12):
            mybtn = playscreen.children[0].children[i]
            #print(mybtn, mybtn.pos, mybtn.size)
            mybtn.add_widget(
                Image(source='images/1111.png', allow_stretch=True))

    def on_press_callback(self, obj):
        total = 0
        for btn in self.btns:
            if btn.state == 'down':
                total += 1
        # print(obj.size,obj.pos)
        obj.add_widget(
            Image(source='images/1111.png', size=obj.size, pos=obj.pos, allow_stretch=True))

    def state_callback(self, obj, value):
        pass

class ScreenApp(App):

    def build(self):
        return GameLayout()

if __name__ == '__main__':
    ScreenApp().run()
