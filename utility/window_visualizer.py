'''
Created on 19 Sep 2016

@author: micra

Extended in May 2019 by Niklas Reusch
'''
from os.path import os

from data_structures import TestCase, OutputPort
import numpy as np

from utility.util import vector_lcm, list_lcm

try:
    import svgwrite
except ImportError:
    pass

class WindowVisualizer(object):
    def __init__(self, s: TestCase):
        '''
        Constructor
        '''
        self.switches = s.switches

        # Static settings
        self.c = {
            'black': 'rgb(0, 0, 0)',
            'white': 'rgb(255, 255, 255)',
            'grey': '#f2f2f2',
            'darkgrey': 'rgb(200, 200, 200)'
        }

        self.s = {}
        self.s['width_scaling'] = 1.7
        self.s['event_line_every'] = 10
        self.s['time_label_distance'] = 50

        self.s['margin'] = (5, 5)
        self.s['margin-right'] = 50
        self.s['font_size'] = 16
        self.s['font_offset'] = (0, -3)
        self.s['row_height'] = 22
        self.s['row_spacing'] = 5
        self.s['label_schedule_spacing'] = 10
        self.s['label_width'] = 180
        self.s['frame_border_width'] = 1

        self.s['sub_offset'] = 3
        self.s['queue_label'] = 'q_{}'

        # Settings
        max_period = 0
        for switch in self.switches.values():
            for port in switch.output_ports.values():
                if max_period < port.get_hyperperiod():
                    max_period = port.get_hyperperiod()

        self.hyperperiod = int(10*max_period)
        self.completion_time = self.hyperperiod
        self.width = int(self.hyperperiod * self.s['width_scaling']) + self.s['label_width'] + self.s['margin'][0] + \
                     self.s['margin-right']  # in pixels

        # Dynamic settings
        self.s['styles'] = {
            'text': 'font-family: times; font-size: {}px'.format(self.s['font_size']),
            'frame_text': 'font-family: times; font-size: 14px',
            'sub_text': 'font-size: 75%;',
            'text-small': 'font-family: times; font-size: 14px',
            'eventline': 'stroke: #c3c3c3;stroke-width: 1;',
            'periodline': 'stroke: #000000;stroke-width: 1;stroke-dasharray: 5, 5',
            'mix': 'fill:#fccecf; stroke: #cc3333; stroke-width: {}'.format(self.s['frame_border_width']),
            'heat': 'fill:#f0f0f0; stroke: #393939; stroke-width: {}'.format(self.s['frame_border_width']),
            'detect': 'fill:#bce6b3; stroke: #166f2b; stroke-width: {}'.format(self.s['frame_border_width']),
            'filter': 'fill:#d1e6ff; stroke: #3a5684; stroke-width: {}'.format(self.s['frame_border_width']),
            'flow': 'fill:#cdcdcd; stroke: #000000; stroke-width: {}'.format(self.s['frame_border_width']),
            'color1': 'fill:#fccef5; stroke: #cc32b2; stroke-width: {}'.format(self.s['frame_border_width']),
            'color2': 'fill:#dccefc; stroke: #6633cc; stroke-width: {}'.format(self.s['frame_border_width']),
            'color3': 'fill:#cefcfb; stroke: #33cbcc; stroke-width: {}'.format(self.s['frame_border_width']),
            'color4': 'fill:#fcf3ce; stroke: #ccb233; stroke-width: {}'.format(self.s['frame_border_width']),
            'color5': 'fill:#defcce; stroke: #66cc33; stroke-width: {}'.format(self.s['frame_border_width']),
            'color6': 'fill:#f0d9e0; stroke: #a55a70; stroke-width: {}'.format(self.s['frame_border_width']),
            'available-queue': 'fill:#ffffff; stroke: #000000; stroke-width: {}; opacity:0.5'.format(
                self.s['frame_border_width']),
            'occupied-queue': 'fill:#666666; stroke: #000000; stroke-width: {}; opacity:0.5'.format(
                self.s['frame_border_width'])
        }

        self.colors = [
            self.s['styles']['mix'],
            self.s['styles']['filter'],
            self.s['styles']['detect'],
            self.s['styles']['color4'],
            self.s['styles']['color3'],
            self.s['styles']['color2'],
            self.s['styles']['color1'],
            self.s['styles']['heat'],
            self.s['styles']['flow'],
            self.s['styles']['color5'],
            self.s['styles']['color6']
        ]

        self.s['row_width'] = self.width - self.s['margin'][0] - self.s['margin-right']
        self.s['schedule_width'] = self.s['row_width'] - self.s['label_width']

        self.draw()

    def create_image(self):
        self.size = (
        self.width, (len(self.rows) + 2) * (self.s['row_height'] + self.s['row_spacing']) + 2 * self.s['margin'][1])

        self.size = (self.size[0], self.size[1] * 1.5)
        self.img = svgwrite.Drawing(size=self.size)

    def draw(self):
        self.period_lines = []
        self.event_lines = set()
        self.rows = []
        self.row_dict = {}

        for switch in self.switches.values():
            for port in switch.output_ports.values():
                r = Row(self, port, switch.uid)
                r.set_label(port)

                self.rows.append(r)
                self.row_dict[port] = r

                self.add_queues(r)

        # Create image with height that fits all rows
        self.create_image()

        if len(self.rows) > 0:
            ypos = 0
            alternative_color = True
            for r in self.rows:
                alternative_color = not alternative_color
                r.draw(ypos, alternative_color)
                ypos += r.get_total_height() + self.s['row_spacing']

            last_row = r

            for each in self.rows:
                each.add_queues()

            for l in self.period_lines:
                l.add(last_row)

    def scale(self, n):
        ratio = self.s['schedule_width'] / self.completion_time
        return ratio * n

    def export(self, to_file):
        directory = os.path.dirname(to_file)
        if directory != '' and not os.path.exists(directory):
            os.makedirs(directory)
        self.img.saveas(to_file)

    def add_queues(self, row):
        port = row.port
        j = 0
        for port_queue_id in port.get_sorted_queuenrs():
            queue = Queue(self, row, port_queue_id, j)
            row.set_queue(queue)

            queue_window = port.get_window(port_queue_id)
            offset = int(queue_window[0])
            end = int(queue_window[1])
            period = int(queue_window[2])

            for i in range(int(self.hyperperiod/period)):
                self.period_lines.append(PeriodLine(self, i * period, row))
                occupation = QueueOccupation(self, queue, self.colors[j], [offset + i*period, end + i*period])
                queue.set_occupation(occupation)
            j += 1


class Row(object):
    def __init__(self, drw, port, switch_name):
        self.drw = drw
        self.position = None
        self.size = (self.drw.s['row_width'], self.drw.s['row_height'])
        self.color = None
        self.label = None
        self.port = port
        self.switch_name = switch_name
        self.frames = []
        self.queues = []  # a list of queue occupations.
        self.text_padding = (
        0, (self.size[1] - self.drw.s['font_size']) / 2 + self.drw.s['font_size'] + self.drw.s['font_offset'][1])

    def set_label(self, label):
        self.label = label

    def add_label(self):
        if self.label:
            position = (self.position[0] + self.drw.s['label_width'] - self.drw.s['label_schedule_spacing'],
                        self.position[1] + self.text_padding[1])
            style = self.drw.s['styles']['text']

            text = self.drw.img.text('',
                                     insert=position,
                                     style=style,
                                     text_anchor='end')
            if isinstance(self.label, OutputPort.OutputPort):
                ycorrection = 0
                text.add(self.drw.img.tspan('['))

                fields = [self.switch_name, self.port.name]

                for i, field in enumerate(fields):
                    if i != 0:
                        text.add(self.drw.img.tspan(', ', dy=[-ycorrection]))
                        ycorrection = 0

                    if '_' in field:
                        try:
                            base, sub = field.split('_')
                            text.add(self.drw.img.tspan(base, dy=[-ycorrection], style='font-style:italic;'))
                            ycorrection = self.drw.s['sub_offset']
                            text.add(self.drw.img.tspan(sub, style=self.drw.s['styles']['sub_text'], dy=[ycorrection]))
                        except ValueError:
                            text.add(self.drw.img.tspan(field))
                    else:
                        text.add(self.drw.img.tspan(field))
                text.add(self.drw.img.tspan(']', dy=[-ycorrection]))
                ycorrection = 0
            else:
                text.text = str(self.label)
            self.drw.img.add(text)

    def get_total_height(self):
        return self.size[1] + sum(q.get_height() for q in self.queues)

    def set_queue(self, queue):
        self.queues.append(queue)

    def add_queues(self):
        for queue in self.queues:
            queue.add()

    def add_background(self):
        self.drw.img.add(
            self.drw.img.rect(insert=self.position, size=(self.size[0], self.get_total_height()), fill=self.color)
        )

    def draw(self, ypos, alternative_color=False):
        color = self.drw.c['grey'] if alternative_color else self.drw.c['white']
        self.position = (self.drw.s['margin'][0],
                         self.drw.s['margin'][1] + ypos)
        self.color = color
        self.add_background()
        self.add_label()


class Line(object):
    def __init__(self, drw, time, style):
        self.drw = drw
        self.time = time
        self.style = style
        self.label = None

    def get_time(self):
        return self.time

    def set_label(self, label):
        self.label = round(label, 2)

    def get_start(self):
        return (self.drw.s['margin'][0] + self.drw.s['label_width'] + self.drw.scale(self.time),
                self.drw.s['margin'][1])

    def get_end(self, last_row):
        y = last_row.position[1] + last_row.get_total_height() + self.drw.s['margin'][1] / 2
        return (self.drw.s['margin'][0] + self.drw.s['label_width'] + self.drw.scale(self.time),
                y)

    def add_label(self, last_row):
        end = self.get_end(last_row)
        position = (end[0],
                    end[1] + self.drw.s['font_size'])
        if self.label != None:
            self.drw.img.add(
                self.drw.img.text(self.label,
                                  insert=position,
                                  style=self.drw.s['styles']['text'],
                                  text_anchor='middle')
            )

    def add(self, last_row):
        self.drw.img.add(
            self.drw.img.line(
                start=self.get_start(),
                end=self.get_end(last_row),
                style=self.style
            )
        )

        self.add_label(last_row)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.time == other.time
        else:
            return False

    def __lt__(self, other):
        if self.time < other.time:
            return True
        elif self.time == other.time:
            return self.__class__.__name__ == 'PeriodLine'
        else:
            return False

    def __hash__(self):
        return hash((self.__class__.__name__, self.time))

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.get_time())


class EventLine(Line):
    def __init__(self, drw, time):
        super().__init__(drw, time, drw.s['styles']['eventline'])


class FrameStartLine(EventLine):
    def __init__(self, drw, frame):
        super().__init__(drw, frame.get_start_time())


class FrameEndLine(EventLine):
    def __init__(self, drw, frame):
        super().__init__(drw, frame.get_end_time())


class PeriodLine(Line):
    def __init__(self, drw, time, row):
        super().__init__(drw, time, drw.s['styles']['periodline'])
        self.row = row

    def get_start(self):
        return (self.drw.s['margin'][0] + self.drw.s['label_width'] + self.drw.scale(self.time),
                self.drw.s['margin'][1] + self.row.position[1])

    def get_end(self, last_row):
        y = last_row.position[1] + last_row.get_total_height() + self.drw.s['margin'][1] / 2
        return (self.drw.s['margin'][0] + self.drw.s['label_width'] + self.drw.scale(self.time),
                self.drw.s['margin'][1] + self.row.position[1] + self.row.get_total_height())


class Frame(object):
    def __init__(self, drw, row, model_frame, period_instance, caption, style):
        self.drw = drw
        self.row = row
        self.model_frame = model_frame
        self.caption = caption
        self.period_instance = period_instance
        self.style = style
        self.start_time = self.model_frame.get_start_time(drw.schedule)
        self.duration = self.model_frame.get_duration()

    def get_start_time(self):
        return self.start_time + self.period_instance * self.model_frame.get_period()

    def get_end_time(self):
        return self.get_start_time() + self.duration

    def get_start_position(self):
        return self.row.position[0] + self.drw.s['label_width'] + self.drw.scale(self.get_start_time())

    def get_width(self):
        return self.drw.scale(self.duration)

    def get_end_position(self):
        return self.get_start_position() + self.get_width()

    def add(self):
        c = self.drw.s['frame_border_width'] / 2
        position = (self.get_start_position() + c,
                    self.row.position[1] + c)
        size = (self.get_width() - 2 * c,
                self.row.size[1] - 2 * c)
        text_position = (position[0] + self.row.text_padding[0] + self.get_width() / 2 - c,
                         position[1] + self.row.text_padding[1] - c)
        self.drw.img.add(
            self.drw.img.rect(insert=position,
                              size=size,
                              style=self.style)
        )
        self.drw.img.add(
            self.drw.img.text(self.caption,
                              insert=text_position,
                              style=self.drw.s['styles']['frame_text'],
                              text_anchor='middle'))


class Queue(object):
    def __init__(self, drw, row, port_queue_id: int, port_queue_nr: int):
        self.drw = drw
        self.row = row
        self.height = row.size[1] / 2
        self.position = None
        self.queue_id = port_queue_id
        self.queue_nr = port_queue_nr
        self.occupations = []
        self.label = self.drw.s['queue_label'].format(port_queue_id)

    def set_occupation(self, occupation):
        self.occupations.append(occupation)

    def add_occupations(self):
        for occupation in self.occupations:
            occupation.add()

    def add_label(self):
        if self.label:
            position = (self.position[0] - self.drw.s['label_schedule_spacing'],
                        self.position[1] + 8)
            style = self.drw.s['styles']['text-small']

            text = self.drw.img.text('',
                                     insert=position,
                                     style=style,
                                     text_anchor='end')

            parts = str(self.label).split('_')
            text.add(self.drw.img.tspan(parts[0], style='font-style:italic;'))
            text.add(
                self.drw.img.tspan(parts[1], style=self.drw.s['styles']['sub_text'], dy=[self.drw.s['sub_offset']]))
            self.drw.img.add(text)

    def add(self):
        self.position = (self.row.position[0] + self.drw.s['label_width'],
                         self.row.position[1] + self.row.size[1] + self.height * self.queue_nr)
        self.add_label()
        self.add_occupations()

    def get_height(self):
        return self.height


class QueueOccupation(object):
    def __init__(self, drw, queue, style, interval):
        self.drw = drw
        self.queue = queue
        self.style = style
        self.from_ = interval[0]
        duration = interval[1] - interval[0]
        self.position = None
        self.c = self.drw.s['frame_border_width'] / 2
        self.size = (drw.scale(duration) - 2 * self.c, self.queue.get_height() - 2 * self.c)

    def add(self):
        self.position = (self.queue.position[0] + self.drw.scale(self.from_) + self.c, self.queue.position[1] + self.c)
        self.drw.img.add(
            self.drw.img.rect(insert=self.position, size=self.size, style=self.style)
        )