from copy import deepcopy
from mpf.config_players.plugin_player import PluginPlayer
from mpfmc.core.mc_config_player import McConfigPlayer


class MpfWidgetPlayer(PluginPlayer):
    """

    Note: This class is loaded by MPF and everything in it is in the context of
    MPF.

    """
    config_file_section = 'widget_player'
    show_section = 'widgets'

    def play(self, settings, mode=None, play_kwargs=None, **kwargs):

        if not play_kwargs:
            play_kwargs = kwargs
        else:
            play_kwargs.update(kwargs)

        super().play(settings, mode, play_kwargs)


class McWidgetPlayer(McConfigPlayer):
    """Base class for the Widget Player that runs on the mpf-mc side of things.
    It receives all of its instructions via BCP from an MpfWidgetPlayer
    instance
    running as part of MPF.
    """

    config_file_section = 'widget_player'
    show_section = 'widgets'
    machine_collection_name = 'widgets'

    def play(self, settings, mode=None, caller=None, play_kwargs=None,
             priority=0, **kwargs):

        settings = deepcopy(settings)

        if 'play_kwargs' in settings:
            play_kwargs = settings.pop('play_kwargs')

        if 'widgets' in settings:
            settings = settings['widgets']

        for widget, s in settings.items():

            if play_kwargs:
                s.update(play_kwargs)

            s.update(kwargs)

            try:
                s['priority'] += priority
            except (KeyError, TypeError):
                s['priority'] = priority

            slide = None

            if s['key']:
                key = s['key']
            else:
                key = widget

            if s['target']:
                try:
                    slide = self.machine.targets[s['target']].current_slide
                except KeyError:  # pragma: no cover
                    pass

            if s['slide']:
                try:
                    slide = self.machine.active_slides[s['slide']]
                except KeyError:  # pragma: no cover
                    pass

            if s['action'] == 'remove':
                if slide:
                    slide.remove_widgets_by_key(key)
                else:
                    for target in self.machine.targets.values():
                        for w in target.slide_frame_parent.walk():
                            try:
                                if w.key == key:
                                    w.parent.remove_widget(w)
                            except AttributeError:
                                pass
                        for x in target.screens:
                            for y in x.walk():
                                try:
                                    if y.key == key:
                                        x.remove_widget(y)
                                except AttributeError:
                                    pass

                continue

            if not slide:
                slide = self.machine.targets['default'].current_slide

            if not slide:  # pragma: no cover
                raise ValueError("Cannot add widget. No current slide")

            if s['action'] == 'add':
                slide.add_widgets_from_library(name=widget, mode=mode, **s)

    def get_express_config(self, value):
        return dict(widget=value)

    def clear(self, caller, priority):
        self.remove_widgets(mode=caller)

    def remove_widgets(self, mode):
        # remove widgets from slides
        for slide in self.machine.active_slides.values():
            slide.remove_widgets_by_mode(mode)

        # remove widgets from slide frame parents
        target_list = set(self.machine.targets.values())
        for target in target_list:
            for widget in [x for x in target.parent.children if
                           x.mode == mode]:
                target.parent.remove_widget(widget)


player_cls = MpfWidgetPlayer
mc_player_cls = McWidgetPlayer


def register_with_mpf(machine):
    return 'widget', MpfWidgetPlayer(machine)
