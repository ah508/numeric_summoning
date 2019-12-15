This is a program designed to find the expected number of pulls necessary to acquire a
given set of adventurers on a given banner in Dragalia Lost. The method should be
generalizable to any gacha with a pity system, though certain complex elements such as
orb picking in FEH may make the implementation more difficult.

-----------------------------------------------------------------------------------------
Dependencies
-----------------------------------------------------------------------------------------
To run this program, you'll need a few other things installed:
- Python 3.6+
- numpy
- multiset
    (see: https://pypi.org/project/multiset/)
- bs4 (technically optional, but you'd need to edit some code)
    (see: https://pypi.org/project/beautifulsoup4/)
- pillow (optional)
    (see: https://pypi.org/project/Pillow/)
    
-----------------------------------------------------------------------------------------
Features
-----------------------------------------------------------------------------------------
This program allows you to:
- Scrape the wiki to update pools
- Create and store your own banners
- Simulate pulls on a banner
- Find the expected number of pulls needed to achieve a certain result
- Find the probability of achieving a certain result after a given number of pulls
- Find the number of pulls needed to have a specified probability of having acheived a
  certain result

-----------------------------------------------------------------------------------------
Usage
-----------------------------------------------------------------------------------------
The program is used quite simply by running numeric_summoning.py with the appropriate
arguments, and then inputting the requested information.
For a list of arguments and some brief descriptions of what they do, use
    python numeric_summoning.py -h

-----------------------------------------------------------------------------------------
Method
-----------------------------------------------------------------------------------------
For the purposes of this program, the problem is formulated as a markov chain.
Ordinarily, the state space for a gacha would be prohibitively complex, but we can easily
trim it down to a manageable size by considering only the units that the user wants to
acquire. Here, all possible states are contained within the powerset of the multiset of
units the user wants to acquire. I should specify that "state" in this context refers to
"state of possession." Each of these states has a number of substates defined by the
possible pity levels. In the documentation, "state" is used somewhat liberally, and I
apologize if the distinction between these two concepts becomes blurred. Transition
probabilities between these states are found directly in the case of single pulls, and
through the use of a seperate inhomogenous markov chain for tenpulls. (You could also use
recursive conditioning for this task, but I personally found the matrix approach to be
more useful.) Once the problem is formulated in this way, we can find most of the things
we need by the usual methods - subtracting the submatrix of transient states from the
identity and inverting to find hitting time, and exponentiating to simulate pulls.

-----------------------------------------------------------------------------------------
Disclaimers
-----------------------------------------------------------------------------------------
1. The probabilities used for these computations are not exact. What I have implemented
   is my best guess at how rates are computed - the results are very close to, but not
   identical to, the probabilities listed in game, and results should be veiwed in the
   light of that limitation.

2. "The expected number of pulls needed to achieve a given result" does not mean that you
   have any guarantee of getting that result in that number of pulls. It is an expected
   value, nothing more.

3. The more things you "want" from a banner, the more intensive the calculation gets.
   I don't have any limitation on what you can request, so try not to bite off more than
   your computer can chew.

4. I'm sure there's some other stuff I ought mention, but it's slipping my mind at the
   moment. Uh, in short, I cannot guarantee the accuracy of the results of this program,
   and I'm not responsible for the conclusions you draw from them.