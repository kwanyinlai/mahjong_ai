# Mahjong Simulation Environment and AI Bot

This project is actively in development. 

The original inspiration for this project came from an interest in the relative strength of AI bots in the chess world (like Torch, Stockfish, LeelaChess, AlphaZero) to humans,
alongside a brewing interest in Mahjong I had over the summer. While I have heard similar stories about the prevelance of these bots in other strategy games like Go, having not 
heard of something similar in Mahjong made me interested in pursuing this challenge, and perhaps figuring out why.

As it turns out (and as I soon found out after starting this project), there do exist many Mahjong bots who perform well against humans; my ignorance to their existence was
merely a byproduct of the 'nicheness' of the game of Mahjong. Nevertheless, I am still pursuing this project as a way to frame my self-taught journey in reinforcement learning.

## Features (so far (and planned features))
- [x] Write a Mahjong simulation environment
- [x] Generate recursive algorithm to check for winning Mahjong hands
- [x] Add rule enforcement to all players in the games to force only legal moves
- [x] Create interface for bots to interact with the environment
- [x] Create bot #1 and #2 as baseline bots (simple bot which always say yes or pick a random option)
- [x] Create bot #3 as improved bot (heuristically guided bot using non-ML tools to play game)
- [ ] Create RL bot pre-trained on full/perfect information
* - [x] Define RL interface for bots to implement their own strategies
* - [x] Return encoded game state to the interface to enabled state-based decisions
* - [x] Get legal actions and transitions from particular game states
* - [x] Create adapter to allow our MahjongGame class to take in actions sequentially and simultaneously
* - [x] Enable recreation of MahjongGame(s) from their game states
* - [x] Add additional attributes to our MahjongGame class as necessary and our state encoding
* - [x] Add neural network guided searching using a policy-value network (with policy-value heads)
* - [x] Centralise a shared neural network to enable self play using a MahjongModel class
* - [x] Create experience buffers and batches to enable training of model
* - [x] Policy gradient and value gradient for learning
* - [x] Integrate Monte-Carlo Tree Search to better guide searches
* - [ ] Iron out bugs with reconstructing game states (CURRENTLY WORKING ON)
* - [ ] Add state determinisation from public information, and masking of hidden information based on spectator perspective
* (...) more to come
- [ ] Knowledge distillation to transfer from full to partial information (to reflect real-world Mahjong game)
- [ ] Play test???
(...) more to come

