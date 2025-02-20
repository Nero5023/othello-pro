from enum import Enum
import numpy as np


class Player(Enum):
    BLACK = 0
    WHITE = 1

    def rival(self):
        if self == Player.BLACK:
            return Player.WHITE
        else:
            return Player.BLACK


BLACK_START = np.uint64(0b1000 << 32 | 0b10000 << 24)
WHITE_START = np.uint64(0b1000 << 24 | 0b10000 << 32)

BORDER_MASK = np.uint64(0b11111111 << 56 |
                        0b10000001 << 48 |
                        0b10000001 << 40 |
                        0b10000001 << 32 |
                        0b10000001 << 24 |
                        0b10000001 << 16 |
                        0b10000001 << 8 |
                        0b11111111)

FINAL_BIT = ~np.uint64(0)
FULL_BIT = ~np.uint64(0)

BOARD_SIDE = 8
BOARD_SIZE_LEN = BOARD_SIDE*BOARD_SIDE
PASS_MOVE = BOARD_SIZE_LEN

HISTORY_NUM = 2


# TODO: Handle pass move
class ReversiBoard:
    def __init__(self, black_state=BLACK_START, white_state=WHITE_START):
        self.black_bit = black_state
        self.white_bit = white_state
        self.black_2d = bit_to_2d_array(self.black_bit, BOARD_SIDE, BOARD_SIDE)
        self.white_2d = bit_to_2d_array(self.white_bit, BOARD_SIDE, BOARD_SIDE)

    def bit_state(self, player: Player):
        if player == Player.BLACK:
            return self.black_bit
        else:
            return self.white_bit

    def array2d_state(self, player: Player):
        if player == Player.BLACK:
            return self.black_2d
        else:
            return self.white_2d

    def get_self_rival_bit_tuple(self, player: Player):
        return self.bit_state(player), self.bit_state(player.rival())

    def get_self_rival_array2d_tuple(self, player: Player):
        return self.array2d_state(player), self.array2d_state(player.rival())

    def get_legal_actions(self, player: Player):
        self_s, rival_s = self.get_self_rival_bit_tuple(player)
        legal_moves = bit_to_1d_array(get_legal_moves_bit(self_s, rival_s), BOARD_SIZE_LEN)
        return legal_moves

    def get_self_rival_legal_action_2d_tuple(self, player: Player):
        self_l = self.get_legal_actions(player)
        rival_l = self.get_legal_actions(player.rival())
        return self_l.reshape((BOARD_SIDE, BOARD_SIDE)), rival_l.reshape((BOARD_SIDE, BOARD_SIDE))

    def get_legal_actions_bits(self, player: Player):
        self_s, rival_s = self.get_self_rival_bit_tuple(player)
        return get_legal_moves_bit(self_s, rival_s)

    def get_legal_actions_in_numbers(self, player: Player):
        actions = self.get_legal_actions(player)
        return np.where(actions == 1)

    def take_move(self, player: Player, move):
        if move == PASS_MOVE:
            return ReversiBoard(self.black_bit, self.white_bit)
        bit_move = np.uint64(0b1 << move)
        self_s, rival_s = self.get_self_rival_bit_tuple(player)
        flipped_stones = get_flipped_stones_bit(bit_move, self_s, rival_s)
        self_s |= flipped_stones | bit_move
        rival_s &= ~flipped_stones
        if player == Player.BLACK:
            return ReversiBoard(self_s, rival_s)
        else:
            return ReversiBoard(rival_s, self_s)

    def to_str(self, player: Player = None):
        first_row = '  A B C D E F G H'
        if player is None:
            zip_list = zip(bit_to_1d_array(self.black_bit, BOARD_SIZE_LEN),
                           bit_to_1d_array(self.white_bit, BOARD_SIZE_LEN))
        else:
            zip_list = zip(bit_to_1d_array(self.black_bit, BOARD_SIZE_LEN),
                           bit_to_1d_array(self.white_bit, BOARD_SIZE_LEN),
                           self.get_legal_actions(player))

        # print(zip_list)
        board_ch_list = np.array(list(map(map_tuple_to_ch, zip_list))).reshape(BOARD_SIDE, BOARD_SIDE)
        rep_str_arr = [first_row]
        for index, arr in enumerate(board_ch_list):
            row = '{} {}'.format(index+1, ' '.join(arr))
            rep_str_arr.append(row)
        return '\n'.join(rep_str_arr)

    def to_rotate_flip_str(self, player: Player = None):
        first_row = '  A B C D E F G H'
        if player is None:
            zip_list = zip(bit_to_1d_array(self.black_bit, BOARD_SIZE_LEN),
                           bit_to_1d_array(self.white_bit, BOARD_SIZE_LEN))
        else:
            zip_list = zip(bit_to_1d_array(self.black_bit, BOARD_SIZE_LEN),
                           bit_to_1d_array(self.white_bit, BOARD_SIZE_LEN),
                           self.get_legal_actions(player))

        # print(zip_list)
        board_ch_list = np.array(list(map(map_tuple_to_ch, zip_list))).reshape(BOARD_SIDE, BOARD_SIDE)
        boards = []
        for i in [0, 1, 2, 3]:
            # rotate
            new_board_rotate = np.rot90(board_ch_list, i)
            boards.append(new_board_rotate)
            # flip
            new_board_flip = np.fliplr(new_board_rotate)
            boards.append(new_board_flip)
        board_strs = []
        for board in boards:
            rep_str_arr = [first_row]
            for index, arr in enumerate(board):
                row = '{} {}'.format(index+1, ' '.join(arr))
                rep_str_arr.append(row)
            board_strs.append('\n'.join(rep_str_arr))
        return '\n\n'.join(board_strs)

    # return the player's stable piece
    def get_stable_pieces_bit(self, player: Player):
        rival = player.rival()
        rival_legal_moves = self.get_legal_actions_in_numbers(rival)[0]
        self_stable_piece = self.bit_state(player)
        for move in rival_legal_moves:
            new_board = self.take_move(rival, move)
            self_stable_piece &= new_board.black_bit
        return self_stable_piece

    def get_stable_pieces_2d(self, player: Player):
        stable_bit_piece = self.get_stable_pieces_bit(player)
        return bit_to_2d_array(stable_bit_piece, BOARD_SIDE, BOARD_SIDE)

    # return the board of given player
    def get_border_2d(self, player: Player):
        return bit_to_2d_array(BORDER_MASK & self.bit_state(player), BOARD_SIDE, BOARD_SIDE)


def map_tuple_to_ch(tup):
    black = '●'
    white = '○'
    legal = '×'
    empty = '☐'
    if len(tup) == 2:
        if tup == (1, 0):
            return black
        elif tup == (0, 1):
            return white
        else:
            return empty
    elif len(tup) == 3:
        if tup == (1, 0, 0):
            return black
        elif tup == (0, 1, 0):
            return white
        elif tup == (0, 0, 1):
            return legal
        else:
            return empty

# TODO: Change


left_right_mask = np.uint64(0x7e7e7e7e7e7e7e7e)
top_bottom_mask = np.uint64(0x00ffffffffffff00)
corner_mask = left_right_mask & top_bottom_mask


def bit_to_1d_array(bit, size):
    return np.array(list(reversed((("0" * size) + bin(bit)[2:])[-size:])), dtype=np.uint8)


def bit_to_2d_array(bit, h, w):
    return bit_to_1d_array(bit, h*w).reshape(h, w)


def get_legal_moves_bit(own, enemy):
    legal_moves = np.uint64(0)
    legal_moves |= search_legal_moves_left(own, enemy, left_right_mask, np.uint64(1))
    legal_moves |= search_legal_moves_left(own, enemy, corner_mask, np.uint64(9))
    legal_moves |= search_legal_moves_left(own, enemy, top_bottom_mask, np.uint64(8))
    legal_moves |= search_legal_moves_left(own, enemy, corner_mask, np.uint64(7))
    legal_moves |= search_legal_moves_right(own, enemy, left_right_mask, np.uint64(1))
    legal_moves |= search_legal_moves_right(own, enemy, corner_mask, np.uint64(9))
    legal_moves |= search_legal_moves_right(own, enemy, top_bottom_mask, np.uint64(8))
    legal_moves |= search_legal_moves_right(own, enemy, corner_mask, np.uint64(7))
    legal_moves &= ~(own | enemy)
    return legal_moves


def search_legal_moves_left(own, enemy, mask, offset):
    return search_contiguous_stones_left(own, enemy, mask, offset) >> offset


def search_legal_moves_right(own, enemy, mask, offset):
    return search_contiguous_stones_right(own, enemy, mask, offset) << offset


def get_flipped_stones_bit(bit_move, own, enemy):
    flipped_stones = np.uint64(0)
    flipped_stones |= search_flipped_stones_left(bit_move, own, enemy, left_right_mask, np.uint64(1))
    flipped_stones |= search_flipped_stones_left(bit_move, own, enemy, corner_mask, np.uint64(9))
    flipped_stones |= search_flipped_stones_left(bit_move, own, enemy, top_bottom_mask, np.uint64(8))
    flipped_stones |= search_flipped_stones_left(bit_move, own, enemy, corner_mask, np.uint64(7))
    flipped_stones |= search_flipped_stones_right(bit_move, own, enemy, left_right_mask, np.uint64(1))
    flipped_stones |= search_flipped_stones_right(bit_move, own, enemy, corner_mask, np.uint64(9))
    flipped_stones |= search_flipped_stones_right(bit_move, own, enemy, top_bottom_mask, np.uint64(8))
    flipped_stones |= search_flipped_stones_right(bit_move, own, enemy, corner_mask, np.uint64(7))
    return flipped_stones


def search_flipped_stones_left(bit_move, own, enemy, mask, offset):
    flipped_stones = search_contiguous_stones_left(bit_move, enemy, mask, offset)
    if own & (flipped_stones >> offset) == np.uint64(0):
        return np.uint64(0)
    else:
        return flipped_stones


def search_flipped_stones_right(bit_move, own, enemy, mask, offset):
    flipped_stones = search_contiguous_stones_right(bit_move, enemy, mask, offset)
    if own & (flipped_stones << offset) == np.uint64(0):
        return np.uint64(0)
    else:
        return flipped_stones


def search_contiguous_stones_left(own, enemy, mask, offset):
    e = enemy & mask
    s = e & (own >> offset)
    s |= e & (s >> offset)
    s |= e & (s >> offset)
    s |= e & (s >> offset)
    s |= e & (s >> offset)
    s |= e & (s >> offset)
    return s


def search_contiguous_stones_right(own, enemy, mask, offset):
    e = enemy & mask
    s = e & (own << offset)
    s |= e & (s << offset)
    s |= e & (s << offset)
    s |= e & (s << offset)
    s |= e & (s << offset)
    s |= e & (s << offset)
    return s


def bit_count(bit):
    return bin(bit).count('1')


class GameState:
    @staticmethod
    def INIT_State():
        board = ReversiBoard()
        return GameState(board, Player.BLACK)

    def __init__(self, board: ReversiBoard, to_play: Player):
        self.board = board
        self.to_play = to_play

    def is_legal_action(self, move):
        return self.get_legal_actions()[move]

    def take_move(self, move):
        # TODO:
        # maybe use variable to store get_legal_actions
        # or delete check
        if self.get_legal_actions()[move] == 0:
            raise Exception("not legal action")
        new_board = self.board.take_move(self.to_play, move)
        return GameState(new_board, self.to_play.rival())

    @property
    def is_terminal(self):
        if (self.board.white_bit | self.board.black_bit) == FINAL_BIT:
            return True
        return self.board.get_legal_actions_bits(Player.BLACK) == 0 and self.board.get_legal_actions_bits(Player.WHITE) == 0

    # 65*1 one is pass move
    def get_legal_actions(self):
        legal_actions = self.board.get_legal_actions(self.to_play)
        if np.sum(legal_actions) == 0:
            return np.concatenate((legal_actions, [1]))
        else:
            return np.concatenate((legal_actions, [0]))

    def need_pass(self):
        return self.board.get_legal_actions_bits(self.to_play) == 0

    def winner(self):
        if self.is_terminal:
            if self.board.white_2d.sum() > self.board.black_2d.sum():
                return Player.WHITE
            elif self.board.white_2d.sum() < self.board.black_2d.sum():
                return Player.BLACK
            else:
                return "TIE"
        else:
            return None

    # BLACK win: +1
    # White win: -1
    def winner_score(self):
        if self.is_terminal:
            if self.board.white_2d.sum() > self.board.black_2d.sum():
                return -1
            elif self.board.white_2d.sum() < self.board.black_2d.sum():
                return 1
            else:
                return 0
        else:
            return 0

    @property
    def to_play_factor(self):
        if self.to_play == Player.BLACK:
            return 1
        else:
            return -1


if __name__ == '__main__':
    b = ReversiBoard()
    print(b.get_legal_actions(Player.BLACK))
    print(b.get_legal_actions_in_numbers(Player.BLACK))
    print(b.to_str(Player.BLACK))
    print(b.take_move(Player.BLACK, 44).to_str(Player.WHITE))
    print(bit_to_2d_array(BORDER_MASK, 8, 8))
    new_b = b.take_move(Player.BLACK, 19)
    print(new_b.to_str())
    print(new_b.get_stable_pieces_2d(Player.BLACK))
