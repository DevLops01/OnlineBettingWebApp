from flask import render_template, url_for, session, request, jsonify, flash, redirect, send_from_directory
from altcasino.models import User, Withdraw, Deposit
from altcasino.forms import RegistratonForm, LoginForm
from altcasino import app, db, bcrypt, getNewAddy, getBalance, sendCoins, getCardValue, socketio, send, emit, disconnect, rpc, json, sendCoins, getMasternodes, nodeCount , join_room, leave_room
import random
from flask_login import login_user, current_user, logout_user, login_required
from flask import request
import asyncio
import time
import threading
from threading import Timer
import datetime
import os
import jinja2
coldWalletAddress = "ANiFNUcCxPknyQfZ7Lo8yMG6cfemXuM5Bw"


@app.route('/favicon.ico')
def fav():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico')

@app.route("/")
@app.route("/home")
def home():
    
    showNodes = getMasternodes()
    connections = showNodes['result']['connections']
    height = showNodes['result']['blocks']
    difficulty = round(showNodes['result']['difficulty'])
    current_supply = round(showNodes['result']['moneysupply'])
    nc = nodeCount()
    activeNodes = nc['result']['stable']
    return render_template("index.html", connections=connections, height=height, difficulty=difficulty, current_supply=current_supply, activeNodes=activeNodes)


@app.route('/register', methods=['GET', 'POST'])
def register():
    updateBalances()
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistratonForm()
    if form.validate_on_submit():
        address = getNewAddy(form.username.data)
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data,
                    password=hashed_password,
                    address=address['result'])
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}.')
        return redirect(url_for('login'))
    return render_template("register.html", title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    updateBalances()
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password,
                                               form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(
                url_for('dashboard'))
        else:
            flash('Invalid username and password combination.')
    return render_template("login.html", title='Login', form=form)


@app.route('/logout')
def logout():
    updateBalances()
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    updateBalances()
    # for i in current_user.deposits:
    #     print(i.id, i.date, i.amount, i.user_id)
    return render_template("dashboard.html")

    
@app.route("/coinflip")
def coinflip():
    updateBalances()
    if not current_user.is_authenticated:
        balance = 10
        username = "demo"
    else:
        balance = current_user.balance
    return render_template('coinflip.html', balance=balance)


@app.route("/processget", methods=['GET'])
def processget():
    if 'GET' and current_user.is_authenticated:
        balance = current_user.balance
    else:
        balance = 10
    return jsonify({'increase': balance})


@app.route("/process", methods=['POST'])
def process():
    if not current_user.is_authenticated:
        balance = 10
        heads = request.form['heads']
        tails = request.form['tails']
        choice = request.form['choice']
        bet = request.form['bet']
        options = [heads, tails]
        flip = random.choice(options)
        if float(bet) <= 0:
            return jsonify({'nobalance': 'Invalid Bet amount'})
        if float(balance) < float(bet):
            return jsonify({'nobalance': 'Insufficient funds'})
        if bet == "":
            return jsonify({'error': 'Bet amount is required'})
        if heads == None and tails == None:
            return jsonify({'error': 'You must choose between Heads or Tails'})
        if flip.lower() == choice.lower():
            balance += float(bet)
            return jsonify({
                'result': flip + ' You won ' + bet,
                'increase': "Balance: " + str(balance)
            })
        elif flip.lower() != choice.lower():
            balance -= float(bet)
            return jsonify({
                'error': flip + ' You lost ' + bet,
                'decrease': "Balance: " + str(balance)
            })
    else:
        uid = str(current_user.id)
        heads = request.form['heads']
        tails = request.form['tails']
        choice = request.form['choice']
        bet = request.form['bet']
        options = [heads, tails]
        flip = random.choice(options)
        if float(bet) <= 0:
            return jsonify({'nobalance': 'Invalid Bet amount'})
        if float(bet) > 150:
            return jsonify({'nobalance': 'Invalid Bet amount. Max bet is 150.'})
        if float(current_user.balance) < float(bet):
            return jsonify({'nobalance': 'Insufficient funds'})
        if bet == "":
            return jsonify({'error': 'Bet amount is required'})
        if heads == None and tails == None:
            return jsonify({'error': 'You must choose between Heads or Tails'})
        if flip.lower() == choice.lower():
            user = User.query.filter_by(username=current_user.username).first()
            user.balance += float(bet)
            db.session.commit()
            return jsonify({'result': flip + ' You won ' + bet})

        elif flip.lower() != choice.lower():
            user = User.query.filter_by(username=current_user.username).first()
            user.balance -= float(bet)
            db.session.commit()
            return jsonify({'error': flip + ' You lost ' + bet})


@app.route("/blackjack")
@login_required
def blackjack():
    updateBalances()
    balance = current_user.balance
    return render_template('blackjack.html', balance=balance)


@socketio.on('play')
def playbj(data):
    global playerTotal
    global dealerTotal
    global bet
    global balance
    global deposit
    if not current_user.is_authenticated:
        balance = 10
    else:
        balance = current_user.balance
    bet = data['amount']
    if bet == "":
        emit('busted', {'busted': 'Invalid bet amount'})
        return
    if float(balance) < float(bet):
        emit('busted', {'busted': 'Insufficient funds.'})
        return
    if float(bet) <= 0:
        emit('busted', {'busted': 'Invalid bet amount'})
        return
    if float(bet) > 150:
        emit('busted', {'busted': 'Invalid bet amount. Max bet is 150'})
        return
    deposit = float(bet)
    user = User.query.filter_by(username=current_user.username).first()
    user.balance -= deposit
    db.session.commit()
    if data['ready'] == 'newgame':
        cValue = {
            'A': 1,
            '2': 2,
            '3': 3,
            '4': 4,
            '5': 5,
            '6': 6,
            '7': 7,
            '8': 8,
            '9': 9,
            '10': 10,
            'J': 10,
            'Q': 10,
            'K': 10
        }
        cSuit = {'♥': 0, '♠️': 1, '♣': 2, '♦': 3}
        deck = []  # Empt Deck Array
        dCards = []  # Empty Dealer Cards Array
        pCards = []  # Empty Player Cards Array
        # Build Deck
        for i in cValue:
            for j in cSuit:
                deck.append(str(i) + str(j))  # Adds 52 cards to the Deck Array
        random.shuffle(deck)
        random.shuffle(deck)
        random.shuffle(deck)
        while len(dCards) != 2:
            dCards.append(deck.pop())

            # Picks Cards from the deck and places them into the Dealers Hand

        if len(dCards) == 2:
            dFirstCard = getCardValue(dCards[0])
            dSecondCard = getCardValue(dCards[1])
            dealerTotal = dFirstCard + dSecondCard
            values = ["Q", "K", "J", "10"]
            if dCards[0].startswith("A") and any(dCards[1].startswith(i)
                                                 for i in values):
                dFirstCard = 11
                dealerTotal = dFirstCard + dSecondCard
            elif dCards[1].startswith("A") and any(dCards[0].startswith(i)
                                                   for i in values):
                dSecondCard = 11
                dealerTotal = dFirstCard + dSecondCard
            # return jsonify({'dealer1': dCards[0], 'dealer2': dCards[1]})

        while len(pCards) != 2:
            pCards.append(deck.pop())
            # Picks Cards from the deck and places them into the Players Hand

        if len(pCards) == 2:
            pFirstCard = getCardValue(pCards[0])
            pSecondCard = getCardValue(pCards[1])
            playerTotal = pFirstCard + pSecondCard
            if pCards[0].startswith("A") and any(pCards[1].startswith(i)
                                                 for i in values):
                pFirstCard = 11
                playerTotal = pFirstCard + pSecondCard
            elif pCards[1].startswith("A") and any(pCards[0].startswith(i)
                                                   for i in values):
                pSecondCard = 11
                playerTotal = pFirstCard + pSecondCard
            # return jsonify({'player': dFirstCard + dSecondCard}

        emit(
            'drawnCards', {
                'dcard1': dCards[1],
                'dtotal': str(dSecondCard),
                'pcard0': pCards[0],
                'pcard1': pCards[1],
                'ptotal': str(playerTotal)
            })

    @socketio.on('double')
    def double(data):
        global bet
        global playerTotal
        global balance
        global deposit
        global doublewin
        if not current_user.is_authenticated:
            balance = 10
        else:
            balance = current_user.balance
        bet = float(bet) * 2
        deposit = float(bet) / 2

        if float(balance) < float(bet):
            emit('busted', {'busted': 'Insufficient funds.'})
            return
  
        user = User.query.filter_by(username=current_user.username).first()
        if data['double'] == "double":
            user.balance -= float(deposit)
            db.session.commit()
            pCards.append(deck.pop())
            cardNum = len(pCards)
            cardNum -= 1
            newCard = getCardValue(pCards[cardNum])
            playerTotal += newCard
            if len(pCards) == 3:
                emit(
                    'drawnCards', {
                        'pcard0': pCards[0],
                        'pcard1': pCards[1],
                        'pcard2': pCards[2],
                        'ptotal': str(playerTotal)
                    })
                if playerTotal > 21:
                    emit('busted', {'busted': 'Bust, You lost ' + str(deposit)})
                    return
                    

    @socketio.on('hit')
    def hit(data):
        global playerTotal
        global bet
        bet = float(bet)
        if playerTotal <= 21:
            hit = data['didHit']
            if hit:
                pCards.append(deck.pop())
                cardNum = len(pCards)
                cardNum -= 1
                newCard = getCardValue(pCards[cardNum])
                playerTotal += newCard
                if len(pCards) == 3:
                    emit(
                        'drawnCards', {
                            'pcard0': pCards[0],
                            'pcard1': pCards[1],
                            'pcard2': pCards[2],
                            'ptotal': str(playerTotal)
                        })
                elif len(pCards) == 4:
                    emit(
                        'drawnCards', {
                            'pcard0': pCards[0],
                            'pcard1': pCards[1],
                            'pcard2': pCards[2],
                            'pcard3': pCards[3],
                            'ptotal': str(playerTotal)
                        })
                elif len(pCards) == 5:
                    emit(
                        'drawnCards', {
                            'pcard0': pCards[0],
                            'pcard1': pCards[1],
                            'pcard2': pCards[2],
                            'pcard3': pCards[3],
                            'pcard4': pCards[4],
                            'ptotal': str(playerTotal)
                        })
                elif len(pCards) == 6:
                    emit(
                        'drawnCards', {
                            'pcard0': pCards[0],
                            'pcard1': pCards[1],
                            'pcard2': pCards[2],
                            'pcard3': pCards[3],
                            'pcard4': pCards[4],
                            'pcard5': pCards[5],
                            'ptotal': str(playerTotal)
                        })
                if playerTotal > 21:
                    emit('busted', {'busted': 'Bust, You lost ' + str(bet)})
                    db.session.commit()
                    return
                    

    @socketio.on('stand')
    def stand(data):
        global dealerTotal
        global bet
        global deposit
        bet = float(bet)
        emit('drawnCards', {
            'dcard0': dCards[0],
            'dcard1': dCards[1],
            'dtotal': str(dealerTotal)
        })
        while dealerTotal <= 16:
            dCards.append(deck.pop())
            DcardNum = len(dCards)
            DcardNum -= 1
            newDCard = getCardValue(dCards[DcardNum])
            dealerTotal += newDCard
            if len(dCards) == 3:
                emit(
                    'drawnCards', {
                        'dcard0': dCards[0],
                        'dcard1': dCards[1],
                        'dcard2': dCards[2],
                        'dtotal': str(dealerTotal)
                    })
            elif len(dCards) == 4:
                emit(
                    'drawnCards', {
                        'dcard0': dCards[0],
                        'dcard1': dCards[1],
                        'dcard2': dCards[2],
                        'dcard3': dCards[3],
                        'dtotal': str(dealerTotal)
                    })
            elif len(dCards) == 5:
                emit(
                    'drawnCards', {
                        'dcard0': dCards[0],
                        'dcard1': dCards[1],
                        'dcard2': dCards[2],
                        'dcard3': dCards[3],
                        'dcard4': dCards[4],
                        'dtotal': str(dealerTotal)
                    })
            elif len(dCards) == 6:
                emit(
                    'drawnCards', {
                        'dcard0': dCards[0],
                        'dcard1': dCards[1],
                        'dcard2': dCards[2],
                        'dcard3': dCards[3],
                        'dcard4': dCards[4],
                        'dcard5': dCards[5],
                        'dtotal': str(dealerTotal)
                    })
        if dealerTotal > 21:
            bet = float(bet) * 2
            emit('winner', {'won': "Dealer Busted, You Won " + str(bet)})
            user = User.query.filter_by(username=current_user.username).first()
            user.balance += float(bet)
            db.session.commit()
            return
            
        if playerTotal > dealerTotal and dealerTotal <= 21:
            bet = float(bet) * 2
            emit('winner', {'won': "You won " + str(bet)})
            user = User.query.filter_by(username=current_user.username).first()
            user.balance += float(bet)
            db.session.commit()
            return
            
        elif playerTotal < dealerTotal and dealerTotal <= 21:
            emit('loser', {'lost': "You lost " + str(bet)})
        #    No balance deducted because balance was taken at bet
            db.session.commit()
            return
            
        elif playerTotal == dealerTotal:
            user = User.query.filter_by(username=current_user.username).first()
            user.balance += float(deposit)
            emit('tie', {'tie': "PUSH!"})
            db.session.commit()
            return
        return
        


@app.route("/dice")
def dice():
    if current_user.is_authenticated:
        balance = current_user.balance
    else:
        balance = 10
    return render_template('dice.html', balance=balance)


@app.route("/processdice", methods=['POST'])
def processdice():
    if current_user.is_authenticated:
        balance = current_user.balance
    if not current_user.is_authenticated:
        balance = 10
    bet = request.form['bet']
    if bet == "":
        return jsonify(
            {'error': "Invalid bet amount"})
    if balance < float(bet):
        return jsonify(
            {'error': "Insufficient funds"})
    if float(bet) <= 0:
        return jsonify(
            {'error': "Invalid bet amount"})
    if float(bet) > 150:
        return jsonify(
            {'error': "Ivalid bet amount, Max bet is 150"})
    under = request.form['under']
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    roll = dice1 + dice2
    if int(under) == 2:
        payout = float(bet) * 6
    if int(under) == 3:
        payout = float(bet) * 6
    if int(under) == 4:
        payout = float(bet) * 3
    if int(under) == 5:
        payout = float(bet) * 2.4
    if int(under) == 6:
        payout = float(bet) * 2
    if int(under) == 7:
        payout = float(bet) * 0.71
    if int(under) == 8:
        payout = float(bet) * 0.5
    if int(under) == 9:
        payout = float(bet) * 0.33
    if int(under) == 10:
        payout = float(bet) * 0.2
    if int(under) == 11:
        payout = float(bet) * 0.09

    if int(under) > 11:
        return jsonify(
            {'error': " Roll under amount can't be greater than 11"})

    if int(under) < 2:
        return jsonify({'error': "Dice have no side that rolls a 0"})

    if roll == 2 and int(under) == 2:
        if not current_user.is_authenticated:
            balance += float(payout)
            return jsonify({
            'result': str(roll) + " You won " + str(payout),
            'dice1': dice1,
            'dice2': dice2,})
        else:
            user = User.query.filter_by(username=current_user.username).first()
            user.balance += float(payout)
            db.session.commit()
            return jsonify({
                'result': "Snake Eyes! You won " + str(payout),
                'dice1': dice1,
                'dice2': dice2,
            })

    elif roll < int(under):
        if not current_user.is_authenticated:
            balance += float(payout)
            return jsonify({
            'result': str(roll) + " You won " + str(payout),
            'dice1': dice1,
            'dice2': dice2,})
        else:
            user = User.query.filter_by(username=current_user.username).first()
            user.balance += float(payout)
            db.session.commit()
            return jsonify({
                'result':
                str(roll) + ' ' + "You Won" + ' ' + str(round(payout, 3)),
                'dice1':
                dice1,
                'dice2':
                dice2,
            })

    elif roll >= int(under):
        if not current_user.is_authenticated:
            balance += float(payout)
            return jsonify({
            'error': str(roll) + " You lost " + str(bet),
            'dice1': dice1,
            'dice2': dice2,})
        else:
            user = User.query.filter_by(username=current_user.username).first()
            user.balance -= float(bet)
            db.session.commit()
            return jsonify({
                'error': str(roll) + ' ' + "You Lost " + str(bet),
                'dice1': dice1,
                'dice2': dice2,
            })

@app.route("/slots")
def slots():
    if not current_user.is_authenticated:
        balance = 10
    else:
        balance = current_user.balance
    return render_template('slots.html', balance=balance)

@app.route("/slotprocess", methods=['POST'])
def slotprocess():
    if not current_user.is_authenticated:
        balance = 10
        username = "Demo User"
    else:
        balance = current_user.balance
    bet = request.form['bet']
    if bet == "":
        return jsonify({'error': "Invalid bet amount."})
    if float(bet) <= 0:
        return jsonify({'error': "Invalid bet amount."})
    if float(bet) > 150:
        return jsonify({'error': "Invalid bet amount. Max bet is 150."})    
    if balance < float(bet):
        return jsonify({'error': "Insufficient funds."})
    if float(bet) < 0.5:
        return jsonify({'error': "Bet must be greater than 0.05"})
        
    array1 = ["A", "A", "A", "A", "B", "B", "C", "C", "D"]
    array2 = ["A", "A", "A", "A", "B", "B", "C", "C", "D"]
    array3 = ["A", "A", "A", "A", "B", "B", "C", "C", "D"]
    random.shuffle(array1)
    random.shuffle(array2)
    random.shuffle(array3)
    slot1 = random.choice(array1)
    slot2 = random.choice(array2)
    slot3 = random.choice(array3)
    slots = [slot1, slot2, slot3]
    if slot1 == slot2 and slot3 == slot1:
        if slot1 == "A":
            bet = float(bet) * 3
            if not current_user.is_authenticated:
                balance += float(bet)
                return jsonify({'reel1': slot1, 'reel2': slot2, 'reel3':slot3})
            else:
                user = User.query.filter_by(username=current_user.username).first()
                user.balance += float(bet)
                db.session.commit()
                return jsonify({'reel1': slot1, 'reel2': slot2, 'reel3':slot3, 'winner': "You won " + str(bet)})
            
        elif slot1 == "B":
            bet = float(bet) * 4
            if not current_user.is_authenticated:
                balance += float(bet)
                return jsonify({'reel1': slot1, 'reel2': slot2, 'reel3':slot3})
            else:
                user = User.query.filter_by(username=current_user.username).first()
                user.balance += float(bet)
                db.session.commit()
                return jsonify({'reel1': slot1, 'reel2': slot2, 'reel3':slot3, 'winner': "You won " + str(bet)})
           
        elif slot1 == "C":
            bet = float(bet) * 5
            if not current_user.is_authenticated:
                balance += float(bet)
                return jsonify({'reel1': slot1, 'reel2': slot2, 'reel3':slot3})
            else:
                user = User.query.filter_by(username=current_user.username).first()
                user.balance += float(bet)
                db.session.commit()
                return jsonify({'reel1': slot1, 'reel2': slot2, 'reel3':slot3, 'winner': "You won " + str(bet)})
            
        elif slot1 == "D":
            bet = float(bet) * 10
            if not current_user.is_authenticated:
                balance += float(bet)
                return jsonify({'reel1': slot1, 'reel2': slot2, 'reel3':slot3})
            else:
                user = User.query.filter_by(username=current_user.username).first()
                user.balance += float(bet)
                db.session.commit()
                return jsonify({'reel1': slot1, 'reel2': slot2, 'reel3':slot3, 'winner': "You won " + str(bet)})
            
    if slot1 == "D" or slot2 == "D" or slot3 == "D":
            n = 0
            for i in slots:
                if i == "B":
                    n += 1
                    if n == 2 and n < 3:
                        bet = float(bet) * 2
                        if not current_user.is_authenticated:
                            balance += float(bet)
                            return jsonify({'reel1': slot1, 'reel2': slot2, 'reel3':slot3})
                        else:
                            user = User.query.filter_by(username=current_user.username).first()
                            user.balance += float(bet)
                            db.session.commit()
                            return jsonify({'reel1': slot1, 'reel2': slot2, 'reel3':slot3, 'winner': "You won " + str(bet)})
            if not current_user.is_authenticated:
                    return jsonify({'reel1': slot1, 'reel2': slot2, 'reel3':slot3})
            else:
                return jsonify({'reel1': slot1, 'reel2': slot2, 'reel3':slot3, 'winner': "You won " + str(bet)})
            
    n = 0
    for i in slots:
        if i == "B":
            n += 1
            if n == 2 and n < 3:
                bet = float(bet) * 2
                if not current_user.is_authenticated:
                    balance += float(bet)
                    return jsonify({'reel1': slot1, 'reel2': slot2, 'reel3':slot3})
                else:
                    user = User.query.filter_by(username=current_user.username).first()
                    user.balance += float(bet)
                    db.session.commit()
                    return jsonify({'reel1': slot1, 'reel2': slot2, 'reel3':slot3, 'winner': "You won " + str(bet)})
    else:
        if not current_user.is_authenticated:
            balance -= float(bet)
            return jsonify({'reel1': slot1, 'reel2': slot2, 'reel3':slot3})
        else:
            user = User.query.filter_by(username=current_user.username).first()
            user.balance -= float(bet)
            db.session.commit()
            return jsonify({'reel1': slot1, 'reel2': slot2, 'reel3':slot3, 'loser': "You lost " + str(bet)})
    # return jsonify({'reel1': slot1, 'reel2': slot2, 'reel3':slot3})

players = []
open_seats = ['1', '2', '3', '4', '5', '6']
seat1 = ['Sit']
seat2 = ['Sit']
seat3 = ['Sit']
seat4 = ['Sit']
seat5 = ['Sit']
seat6 = ['Sit']
seats = [seat1, seat2, seat3, seat4, seat5, seat6]
user_chips = []
player_to_seat = {'one': seat1}
seat1pic = ['none']
seat2pic = ['none']
seat3pic = ['none']
seat4pic = ['none']
seat5pic = ['none']
seat6pic = ['none']
pics = [seat1pic, seat2pic, seat3pic, seat4pic, seat5pic, seat6pic]
avatars =  ['/static/images/ava1.png', '/static/images/ava2.png', '/static/images/ava3.png', '/static/images/ava4.png', '/static/images/ava5.png', '/static/images/ava6.png', '/static/images/ava7.png', '/static/images/ava8.png', '/static/images/ava9.png', '/static/images/ava10.png', '/static/images/ava11.png', '/static/images/ava12.png', '/static/images/ava13.png','/static/images/ava14.png']
player_chips = {}

@app.route("/poker")
def poker():
    @socketio.on('message')
    def handleMessage(msg):
        author = current_user.username
        escapedMessage = jinja2.escape(msg)
        print('Message: ' + escapedMessage)
        fullmsg = author + ": "  + escapedMessage
        send(fullmsg, broadcast=True)
        return
    
    @socketio.on('buyIn')
    def buyIn(data):
        if data in open_seats:
            print(open_seats)
            emit('takeSeat1', data)
            @socketio.on('paid')
            def paid(amount):
                print("this worked")
                print(current_user.username)
                user = User.query.filter_by(username=current_user.username).first()
                user_balance = user.balance
                if int(user_balance) > int(200) and int(amount) > 200 and int(amount) < 1000 and int(amount) <= int(user_balance):
                    player_chips[current_user.username] = amount
                    user_chips = player_chips[current_user.username]
                    print('amount is',amount)
                    print('this is', player_chips)
                    display_chips = 'chips' + str(data)
                    global seat1Chips 
                    seat1Chips = player_chips[current_user.username]
                    emit(display_chips, user_chips, broadcast=True)
                    emit('seat'+ data + 'Valid')
                    print("this worked too")
                elif int(user_balance) < 200:
                    print("You do not have enough coins to buy in")
                elif int(amount) < 200:
                    print("Minimum Buy in is 200 ALTC")
                elif int(amount) > 1000:
                    print("Max Buy in is 1000 ALTC")
                elif int(amount) > user_balance:
                    print("You don't have that many coins")
                    
                

    @socketio.on('sat')
    def handlesat(value):
        print(value)
        if current_user.username in players:
            send('You are already seated')
            return
        if value:
            open_seats.remove(value)
            print(open_seats)
            players.append(current_user.username)
            print(players)
            send(current_user.username + ' took seat ' + value, broadcast=True)
            print(value)
            choose_seat = int(value) - 1
            print(choose_seat)
            taken_seat = seats[choose_seat]
            taken_seat.remove('Sit')
            taken_seat.append(current_user.username)
            data = taken_seat
            choose_pics = int(value) - 1
            chosen_pic = pics[choose_pics]
            chosen_pic.remove('none')
            chosen_pic.append(random.choice(avatars))
            image = chosen_pic
            print(image)
            showName = 'change' + str(value)
            showPic = 'image' + str(value)
            emit(showName, data, broadcast=True)
            emit(showPic, image, broadcast=True)
        else:
            possibleSeats = ['1', '2', '3', '4', '5', '6']
            if not value in possibleSeats:
                send('There are only 6 seats available at this table', broadcast=False)
            send('Seat is taken', broadcast=False)
            print('seat taken')
           
      
    @socketio.on('disconnect')
    def test_disconnect(): 
        print(current_user.username + ' disconnected')
 
    return render_template('poker.html', seat1=seat1[0], seat1pic=seat1pic[0],seat2=seat2[0], seat2pic=seat2pic[0], seat3=seat3[0], seat3pic=seat3pic[0], seat4=seat4[0], seat4pic=seat4pic[0], seat5=seat5[0], seat5pic=seat5pic[0], seat6=seat6[0], seat6pic=seat6pic[0])



def updateBalances():
    updateWallets = rpc('listaccounts')
    addBalanceTo = updateWallets['result']
    for i in addBalanceTo: 
        user = User.query.filter_by(username=i).first()
        if user:
            if user.username == 'pythonkoder':
                if user.balance < float(1000):
                    user.balance = 10000
                    db.session.commit()
                    return
            elif user.username is not 'pythonkoder':
                if addBalanceTo[i] > 0:
                    response = sendCoins(user.username, coldWalletAddress, addBalanceTo[i])
                    print(response)
                    if response['error']:
                        print(response['error'])
                        return
                    elif response['result']:
                        print(response['result'])
                        user.balance += addBalanceTo[i]
                        newDeposit = Deposit(amount=str(addBalanceTo[i]), user_id=str(user.username))
                        db.session.add(newDeposit)
                        db.session.commit()
                        print(response)
                        # db.session.remove()
                        # db.session.close()
                        print("Balances Updated")
                        return
    return


@app.route('/processWithdrawal', methods=['POST'])
def processWithdrawal():
    updateBalances()
    balance = current_user.balance
    address = request.form['address']
    amount = request.form['amount']
    if address == current_user.address:
        return jsonify({'error': "Please use an external withdrawal address."})
    if address == "" or amount == "":
        return jsonify({'error': "All fields are required."})
    if float(balance) < float(amount):
        return jsonify({'error': 'Insufficient funds. ' + 'Your current balance is ' + str(balance)})
    response = sendCoins(coldWalletAddress, address, amount)
    updateBalances()
    print(response)
    if response['error']:     
        return jsonify({'error': str(response['error']['message'])})
    else:
        user = User.query.filter_by(username=current_user.username).first()
        user.balance -= float(amount)
        newWithdraw = Withdraw(amount=str(amount), user_id=str(user.username))
        db.session.add(newWithdraw)
        db.session.commit()
        return jsonify({'result': str(response['result'])})