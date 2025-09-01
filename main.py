from mahjong_game import MahjongGame


if __name__ == "__main__":
    game = MahjongGame()
    game.play_round()

    # while not game.win:
    #     game.play_round()
    #     game = MahjongGame()
    # MahjongGame.test_fan_calc()

    # MahjongGame.test_win_scenario()
    # MahjongGame.test_win_claim()

# TODO: Need to play the next player - doesn't work right now
# TODO: Check self draw wins
# TODO: Still major bugs with duplicate tiles
