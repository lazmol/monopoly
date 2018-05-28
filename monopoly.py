import random


class Player():
    # some params
    safety_factor = 1  # 1 = buys as long as there is enough money, 2 = buys when he has twice the money
    buy_every = 1  # 1 = buys every round, 3 = buy 1st chance then skips two chances

    def __init__(self, name):
        self.__name = name
        self.__position = 0  # position on the board
        self.__money = 10000  # init money
        self.__ind_roll = 0  # the order that tells which player rolls first etc
        self.__chances2buy = -1
        self.__estates = []

    def get_name(self):
        return self.__name

    def get_money(self):
        return self.__money

    def set_money(self, diff):
        self.__money += diff

    def get_position(self):
        return self.__position

    def set_position(self, rolled_num, n_fields):
        self.__position = (self.__position + rolled_num) % n_fields

    def get_ind_roll(self):
        return self.__ind_roll

    def set_ind_roll(self, num):
        self.__ind_roll = num

    def add_estate(self, field_estate):
        self.__estates.append(field_estate)

    def eliminate(self):
        for estate in self.__estates:
            estate.abandon()

    def step(self, field_estate):
        self.__chances2buy += 1
        can_buy = self.__chances2buy % self.buy_every == 0
        # self = current player
        estate = field_estate
        owner = estate.get_owner()
        with_house = estate.with_house
        if not owner and can_buy and self.__money >= estate.price_estate * self.safety_factor:
            estate.buy_estate(self)

        elif owner == self:  # player on the field owns it
            if not with_house and can_buy and self.__money >= estate.price_house * self.safety_factor:
                estate.buy_house(self)
        else:  # somebody else owns it
            if owner and with_house:
                fee = (estate.price_estate + estate.price_house) * estate.fee_factor
            elif owner:
                fee = estate.price_estate * estate.fee_factor
            else:
                fee = 0
            if fee:
                print(f"{self.get_name()} stepped on {owner.get_name()}'s estate, had to pay {fee}")
                owner.set_money(fee)
                self.set_money(-1 * fee)


class PlayerGreedy(Player):
    '''Buys estate/house immediately'''
    safety_factor = 1
    buy_every = 1


class PlayerCareful(Player):
    '''Keeps always at least half of his money'''
    safety_factor = 2
    buy_every = 1


class PlayerTactical(Player):
    '''Skips every second buy'''
    safety_factor = 1
    buy_every = 2


class Field():
    '''Prototype Field'''
    def __init__(self, pos):
        self.__pos = pos

    def get_pos(self):
        return self.__pos


class FieldEstate(Field):
    price_estate = 1000
    price_house = 4000
    fee_factor = 0.5  # the amount claimed as fee  from other players (multiplied by price of estate + house)

    def __init__(self, pos):
        super().__init__(pos)
        self.__owner = None
        self.with_house = False

    def get_owner(self):
        return self.__owner

    def abandon(self):
        self.__owner = None
        self.with_house = False

    def buy_estate(self, player):
        self.__owner = player
        player.add_estate(self)
        player.set_money(-1 * self.price_estate)
        print(f'Player: {player.get_name()} bought estate on position: {self.get_pos()}.')

    def buy_house(self, player):
        self.with_house = True
        player.set_money(1 * self.price_house)
        print(f'Player: {player.get_name()} built a house on position: {self.get_pos()}.')

    def act_on_player(self, player):
        player.step(self)

    def sell_estate(self, Player):
        '''Not required'''
        pass


class FieldLuck(Field):
    def __init__(self, pos, prize):
        super().__init__(pos)
        self.__delta_money = prize

    def get_delta_money(self):
        return self.__delta_money

    def act_on_player(self, player):
        player.set_money(self.__delta_money)
        print(f'Player: {player.get_name()} lost/received money on luck/Service field: {self.get_pos()}, {self.__delta_money}')


class FieldService(FieldLuck):
    def __init__(self, pos, cost):
        super().__init__(pos, cost)
        self.__delta_money = -1 * cost  # does not seem to work why??


class Game():
    field_types = [FieldEstate, FieldLuck, FieldService]
    player_types = [PlayerGreedy, PlayerCareful, PlayerTactical]

    def __init__(self):
        self.__fields = self.load_fields()
        self.__n_fields = len(self.__fields)
        self.__players = self.load_players()
        self.__players_ranking = []
        self.__rounds = 0

    def get_fields(self):
        return self.__fields

    def get_players(self):
        return self.__players

    def load_fields(self, inp_file_fields='fields.txt'):
        fields = []
        with open(inp_file_fields, 'rU') as fh:  # skip comment or empty lines
            lines = map(lambda x: x.strip(), fh.readlines())
            lines = [l for l in lines if l and not l.startswith('#')]
        for pos, line in enumerate(lines):
            i_field_type = int(line.strip()[0])
            if i_field_type == 0:  # Estate field is initialized only with pos
                fields.append(FieldEstate(pos))
            else:
                price = int(line.split()[1])
                fields.append(self.field_types[i_field_type](pos, price))
        return fields

    def load_players(self, inp_file_players='players.txt'):
        '''<tactics> <name>'''
        players = []
        with open(inp_file_players, 'rU') as fh:
            for line in fh:  # read lines with generator
                if line.startswith('#') or not line.strip():  # skip comment or empty lines
                    continue
                tact, name = line.split()
                tact = int(tact)
                name = name.strip()
                players.append(self.player_types[tact](name))  # initialize correct class
        return players

    def play(self):
        while len(self.__players_ranking) < (len(self.__players) - 1):  # while the winning order is found
            self.__rounds += 1
            for p in self.__players:
                if p in self.__players_ranking:  # player already eliminated
                    continue
                rolled_num = self.roll_dice()
                p.set_position(rolled_num, self.__n_fields)
                field = self.__fields[p.get_position()]
                field.act_on_player(p)
                if p.get_money() < 0:
                    p.eliminate()
                    print(f'Player {p.get_name()} eliminated in round {self.__rounds} with {p.get_money()} $!')
                    self.__players_ranking.insert(0, p)

        winner = [p for p in self.__players if p not in self.__players_ranking]
        self.__players_ranking.insert(0, winner[0])
        print(f'The game is finished after {self.__rounds} rounds! The ranking:')
        for i, p in enumerate(self.__players_ranking):
            print(f'{i}, {p.get_name()}, {p.get_money()}')

    def roll_dice(self):
        return random.randint(1, 7)

    def turn_order(self):
        '''Find out who rolls first, 2nd etc
        The player who rolled highest starts first.'''
        for p in self.__players:
            p.set_ind_roll(self.roll_dice())
        indices_roll = [p.get_ind_roll() for p in self.__players]
        while len(set(indices_roll)) < len(indices_roll):
            for ind, count in Counter(indices_roll):
                indices_roll = [p.get_ind_roll() for p in self.__players]


if __name__ == '__main__':
    # pl = Player('asdf')
    # print(pl.__nev)  # Python renames it to _Player__nev to make it private!!
    # print(dir(pl))
    # pl.__getattr__('__name')  # ???
    monop = Game()
    monop.play()
