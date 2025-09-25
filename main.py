from ai_bot import BasicBot
from mahjong_game import MahjongGame
from mahjong_table import MahjongTable

if __name__ == "__main__":
    table = MahjongTable()
    table.start_table()
    for player in table.players:
        print(f"Final score for Player {player.player_id}: {player.score}")

    # game = MahjongGame([BasicBot(i) for i in range(4)], "east")
    # game.play_round()

    # while not game.win:
    #     game.play_round()
    #     game = MahjongGame()
    # MahjongGame.test_fan_calc()

    # MahjongGame.test_win_scenario()
    # MahjongGame.test_win_claim()
