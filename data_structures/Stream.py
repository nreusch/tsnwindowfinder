class Stream(object):
    def __init__(self, uid: 'unique name',  size: 'data size (byte)', deadline: 'Deadline', period: 'period', priority: 'priority',  route: 'route'):
        self.uid = uid
        self.size = size
        self.deadline = deadline
        self.route = route
        self.period = period
        self.priority = priority

        # 1 Byte takes 0.008us at 1000Mbits, 42bit header for ethernet packet
        self.sending_time = (self.size+42)*0.008

    def __repr__(self):
        rtstring = ''
        for node in self.route:
            rtstring += node.uid + '->'
        rtstring = rtstring[:-2]
        return 'Stream(UID: {}, DataSize: {}Byte, Deadline: {}us, Period: {}us, Priority: {}, Route:{})'.format(self.uid, self.size, self.deadline, self.period, self.priority, rtstring)
        

