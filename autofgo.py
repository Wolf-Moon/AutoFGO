import abc
import numpy as np
import random
import time
import uiautomator2 as u2
import win32gui
import win32ui

from ctypes import windll
from PIL import Image
from skimage.feature import match_template
from typing import Union, List

#自定义模块
from util import getDomColor, getNum

class UA2Handler:
    def __init__(self, device, screenShotter=None):
        self.driver = u2.connect(device)
        self.screenShotter = screenShotter
        self.screenShot = None

    def tap(self, pos):
        tapPosX = max(pos[0], min(pos[2], round(random.gauss((pos[0]+pos[2]) / 2, (pos[2] - pos[0]) / 5.5))))
        tapPosY = max(pos[1], min(pos[3], round(random.gauss((pos[1]+pos[3]) / 2, (pos[3] - pos[1]) / 5.5))))
        self.driver.click(tapPosX, tapPosY)

    def swipe(self, start, end=None, direction="up", distance=0, duration=None):
        if duration is not None:
            duration = max(duration[0], min(duration[1], random.gauss((duration[0]+duration[1]) / 2, (duration[1] - duration[0]) / 5.5)))
        if end is not None:
            self.driver.swipe(start[0], start[1], end[0], end[1], duration)
        elif direction == "up":
            self.driver.swipe(start[0], start[1], start[0], start[1] - distance, duration)
        elif direction == "down":
            self.driver.swipe(start[0], start[1], start[0], start[1] + distance, duration)
        elif direction == "left":
            self.driver.swipe(start[0], start[1], start[0] - distance, start[1], duration)
        elif direction == "right":
            self.driver.swipe(start[0], start[1], start[0] + distance, start[1], duration)
        return duration if duration else 55*0.05

    def shotScreen(self):
        if self.screenShotter is None:
            self.screenShot = self.driver.screenshot()
        else:
            self.screenShot = self.screenShotter.screenshot()

class Screenshotter:

    def __init__(self, windowSize, cropRect, windowTitle):
        self.windowSize = windowSize
        self.cropRect = cropRect
        self.hwnd = win32gui.FindWindow(None, windowTitle)

        self.hwndDC = win32gui.GetWindowDC(self.hwnd)
        self.mfcDC = win32ui.CreateDCFromHandle(self.hwndDC)
        self.saveDC = self.mfcDC.CreateCompatibleDC()

        self.saveBitMap = win32ui.CreateBitmap()
        self.saveBitMap.CreateCompatibleBitmap(self.mfcDC, windowSize[0], windowSize[1])

        self.saveDC.SelectObject(self.saveBitMap)

    def __del__(self):
        win32gui.DeleteObject(self.saveBitMap.GetHandle())
        self.saveDC.DeleteDC()
        self.mfcDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, self.hwndDC)


    def screenshot(self):
        result = windll.user32.PrintWindow(self.hwnd, self.saveDC.GetSafeHdc(), 0)

        bmpinfo = self.saveBitMap.GetInfo()
        bmpstr = self.saveBitMap.GetBitmapBits(True)

        im = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)
        im = im.crop(self.cropRect)
        im = im.resize((1920, 1080))
        if result == 1:
            return im
        else:
            return None

class Element:

    def __init__(self, position: tuple, driver: UA2Handler):
        self.position = position
        self.driver = driver

    def setPosition(self, pos):
        self.position = pos

    def tap(self):
        self.driver.tap(self.position)

    def saveImg(self, name):
        self.driver.screenShot.crop(self.position).save(name)


class FGOElement(Element):

    def __init__(self, position: tuple, template: Union[str, None], driver: UA2Handler, aiDetectCategory: Union[str, None]=None):
        super(FGOElement, self).__init__(position, driver)
        if template is not None:
            self.template = Image.open(template)
        else:
            self.template = None
        self.aiDetectCategory = aiDetectCategory


    def matchTemplate(self, shot=True, saveImg=True, returnDetails=False, aiDetect=False):
        if shot:
            self.driver.shotScreen()
        matchImg = self.driver.screenShot.crop(self.position)
        #print(f"{matchImg.size},{self.driver.screenShot.size},{self.position}, {self.position[2]-self.position[0]}")
        if saveImg:
            matchImg.save("cropImg.png")
        if aiDetect:
            pass
        else:
            res = match_template(np.array(matchImg), np.array(self.template))
            result = np.max(res)
            if result >= 0.95:
                if returnDetails:
                    return True, res
                else:
                    return (True, )
            else:
                if returnDetails:
                    return False, res
                else:
                    return (False, )

    def detect(self, maxWaitTime=5, detectFreq=0.5, shot=True, wait=(2, 3), returnDetails=False, aiDetect=False):
        assert self.template is not None
        acturalDetectTime = 0
        while True:
            detectTime = time.perf_counter()
            res = self.matchTemplate(shot=shot, returnDetails=returnDetails, aiDetect=aiDetect)
            if res[0]:
                if wait:
                    time.sleep(random.uniform(*wait))
                if returnDetails:
                    return True, res[1]
                else:
                    return True

            detectTime = time.perf_counter() - detectTime
            acturalDetectTime += detectTime
            if acturalDetectTime >= maxWaitTime:
                break
            time.sleep(max(0, detectFreq-detectTime))
        if returnDetails:
            return False, res[1]
        else:
            return False


class CardAnalyser:

    def __init__(self, servantsTemplate, assistantTagPath, assistantServantName, unknownServantName="未知", strategy=None, fgoHandler=None,
                 startStarRect=(28, 494, 274, 596),
                 startServantRect=(95, 611, 259, 744),
                 startAssistantRect=(207, 611, 360, 675),
                 startTypeRect=(83, 789, 307, 915),
                 step=386):
        self.fgoHandler =fgoHandler
        self.servantsTemplate = {k: Image.open(v) for k, v in servantsTemplate.items()}
        self.assistantTag = Image.open(assistantTagPath)
        self.assistantServantName = assistantServantName
        self.unknownServantName = unknownServantName
        self.strategy = strategy if strategy else []
        self.result = {}

        self.startStarRect = startStarRect
        self.startServantRect = startServantRect
        self.startAssistantRect = startAssistantRect
        self.startTypeRect = startTypeRect
        self.step = step

    def setStrategy(self, strategy):
        self.strategy = strategy


    def starAnalysis(self, No, img):
        self.result[f"star{No}"] = getNum(img)

    def servantAnalysis(self, No, img, assImg):
        res = np.max(match_template(np.array(assImg), np.array(self.assistantTag)))
        if res > 0.9:
            self.result[f"servant{No}"] = self.assistantServantName
            return
        for servantName, template in self.servantsTemplate.items():
            res = match_template(np.array(img), np.array(template))
            result = np.max(res)
            if result >= 0.95:
                self.result[f"servant{No}"] = servantName
                return
        self.result[f"servant{No}"] = self.unknownServantName

    def cardTypeAnalysis(self, No, img):
        result = getDomColor(img)
        if result == 0:
            self.result[f"cardType{No}"] = "Buster"
        elif result == 1:
            self.result[f"cardType{No}"] = "Quick"
        else:
            self.result[f"cardType{No}"] = "Arts"

    def analyseCards(self, screenshot=True):
        assert screenshot is not None or self.fgoHandler is not None
        if screenshot is None:
            self.fgoHandler.shotScreen()
            screenshot = self.fgoHandler.screenShot
        for No in range(5):
            starImg = screenshot.crop((self.startStarRect[0]+self.step*No, self.startStarRect[1], self.startStarRect[2]+self.step*No, self.startStarRect[3]))
            servantImg = screenshot.crop((self.startServantRect[0]+self.step*No, self.startServantRect[1], self.startServantRect[2]+self.step*No, self.startServantRect[3]))
            cardTypeImg = screenshot.crop((self.startTypeRect[0]+self.step*No, self.startTypeRect[1], self.startTypeRect[2]+self.step*No, self.startTypeRect[3]))
            assistantImg = screenshot.crop((self.startAssistantRect[0]+self.step*No, self.startAssistantRect[1], self.startAssistantRect[2]+self.step*No, self.startAssistantRect[3]))
            self.starAnalysis(No, starImg)
            self.servantAnalysis(No, servantImg, assistantImg)
            self.cardTypeAnalysis(No, cardTypeImg)

        return [
            (self.result["servant0"], self.result["cardType0"], self.result["star0"]),
            (self.result["servant1"], self.result["cardType1"], self.result["star1"]),
            (self.result["servant2"], self.result["cardType2"], self.result["star2"]),
            (self.result["servant3"], self.result["cardType3"], self.result["star3"]),
            (self.result["servant4"], self.result["cardType4"], self.result["star4"]),
        ]

    def _cardParse(self, cardList, rule, selected):
        score = [[i, card[2]] for i, card in enumerate(cardList)]
        for i, card in enumerate(cardList):
            if i + 4 in selected:
                score[i][1] = -1
                continue
            if card[2] * 100 < int(rule[2]):
                score[i][1] = -1
                continue
            if rule[1].lower() != "any" and card[1].lower() != rule[1].lower():
                score[i][1] = -1
                continue
            if rule[0].lower() != "any" and card[0].lower() != rule[0].lower():
                score[i][1] = -1
                continue
        score.sort(key=lambda x:x[1], reverse=True)
        return score


    def cardSelect(self, screenshot=None, selectedCard=None):
        '''
        rule sample
        rule =[
            "仇凛 Buster -1",      #仇凛红卡
            "any Buster -1",      #没有的话就任意红卡
            "仇凛 any 30",        #没有的话就任意暴击率大于30%的仇凛的卡
            "any any 30",        #没有的话就任意暴击率大于30%的卡
            "any Arts -1",        #没有的话就任意蓝卡
            "any any -1"          #都没有就按暴击星数量选卡
                                #还选不出来就会随机选卡
        ]
        '''
        cardList = self.analyseCards(screenshot)
        ruleList = [tuple(x.split(" ")) for x in self.strategy]
        if selectedCard is None:
            selectedCard = []
        cardSelectedByComputer = []
        for rule in ruleList:
            if len(selectedCard) >= 3:
                break
            scores = self._cardParse(cardList, rule, selectedCard)
            for pos, score in scores:
                if score < 0:
                    break
                cardSelectedByComputer.append(pos + 4)
                selectedCard.append(pos + 4)
                if len(selectedCard) >= 3:
                    break
        return cardSelectedByComputer, [cardList[i-4] for i in cardSelectedByComputer]


class FGOAutoRun:

    def __init__(self, deviceUrl: str, screenShotter=None):
        self.runTimes = 50
        self.useApple = True
        self.fgoHandler = UA2Handler(deviceUrl, screenShotter)
        self.elements = {}
        self.initElement()

    def setConfig(self, runTimes: int=50, useApple: bool=True):
        self.runTimes = runTimes
        self.useApple = useApple

    def createElement(self, name: str, posRect: tuple, template: Union[str, None], driver: UA2Handler):
        assert self.elements.get(name, None) is None
        self.elements[name] = FGOElement(posRect, template, driver)

    def getElement(self, name):
        return self.elements.get(name, None)

    def tap(self, name, *args, **kwargs):
        self.getElement(name).tap(*args, **kwargs)

    def detect(self, name, *args, **kwargs):
        return self.getElement(name).detect(*args, **kwargs)

    def detectBattleUI(self, maxDetectTime=100):
        return self.detect("MasterSkillBtn", maxDetectTime)

    def targetlessServantSkill(self, servantPos:int, skillPos:int, withDetect=True, wait=(2, 3), speedup=True):
        assert servantPos in [1,2,3] and skillPos in [1,2,3]
        if withDetect:
            self.detect("MasterSkillBtn", 100, wait=wait)
        self.tap(f"Skill_{servantPos}_{skillPos}")
        if speedup:
            self.wait(0.1, 0.15)
            self.tap("AnyWhere")

    def targetServantSkill(self, servantPos, skillPos, targetPos, withDetect=True, wait=(2, 3), speedup=True):
        assert targetPos in [1, 2, 3]
        self.targetlessServantSkill(servantPos, skillPos, withDetect, wait, speedup=False)
        self.wait(0.8, 1.1)
        self.tap(f"SkillAllyTarget{targetPos}")
        if speedup:
            self.wait(0.1, 0.15)
            self.tap("AnyWhere")

    def targetLessMasterSkill(self, skillPos, withDetect=True, wait=(2, 3), speedup=True):
        assert skillPos in [1,2,3]
        if withDetect:
            self.detect("MasterSkillBtn", 100, wait=wait)
        self.tap("MasterSkillBtn")
        self.wait(0.5, 0.8)
        self.tap(f"MasterSkill{skillPos}")
        if speedup:
            self.wait(0.1, 0.15)
            self.tap("AnyWhere")

    def targetMasterSkill(self, skillPos, targetPos, withDetect=True, wait=(2, 3), speedup=True):
        assert targetPos in [1, 2, 3]
        self.targetLessMasterSkill(skillPos, withDetect, wait, speedup=False)
        self.wait(0.8, 1.1)
        self.tap(f"SkillAllyTarget{targetPos}")
        if speedup:
            self.wait(0.1, 0.15)
            self.tap("AnyWhere")

    def orderChangeSkill(self, targetPos1, targetPos2, speedup=True):
        assert targetPos1 in [1, 2, 3] and targetPos2 in [1, 2, 3]
        self.targetLessMasterSkill(3)
        time.sleep(random.uniform(1, 1.5))
        self.tap(f"orderChange{targetPos1}")
        time.sleep(random.uniform(0.2, 0.5))
        self.tap(f"orderChange{targetPos2}")
        time.sleep(random.uniform(0.2, 0.5))
        self.tap("changeBtn")
        if speedup:
            self.wait(0.1, 0.15)
            self.tap("AnyWhere")

    def atkAndSelectOrderCard(self, cardList: List[int], cardAnalyser=None, mode="prefix", speedup=True):
        assert len(cardList) <= 3

        self.detect("ATKBtn", 100, wait=(0.5, 0.7), detectFreq=0)
        self.tap("ATKBtn")
        self.wait(1, 1)
        selectableCard = [4, 5, 6, 7, 8]
        selectTime = time.perf_counter()
        if cardAnalyser is not None:
            orderCardPos, orderCards = cardAnalyser.cardSelect(selectedCard=cardList[:])
            print(orderCards)
            if mode == "prefix":
                cardList = cardList + orderCardPos
            elif mode == "suffix":
                cardList = orderCardPos + cardList
            elif mode == "mid" and len(cardList) == 1:
                cardList = [orderCardPos[0], cardList[0], orderCardPos[1]]
            else:
                cardList.insert(1, orderCardPos[0])
        for card in cardList[::-1]:
            if card > 3:
                selectableCard.remove(card)
        for _ in range(3 - len(cardList)):
            if mode == "prefix":
                cardList.append(0)
            elif mode == "suffix":
                cardList.insert(0, 0)
            elif mode == "mid" and len(cardList) == 1:
                cardList = [0, cardList[0], 0]
            else:
                cardList.insert(1, 0)
        selectTime = time.perf_counter()-selectTime
        print(f"计算选卡耗时：{selectTime}")
        for card in cardList:
            if card == 0:
                card = random.choice(selectableCard)
                selectableCard.remove(card)
            if card < 4:
                self.tap(f"SpCard{card}")
            else:
                self.tap(f"Card{card-3}")
            self.wait(0.2, 0.3)

    def wait(self, minTime, maxTime):
        time.sleep(random.uniform(minTime, maxTime))

    def skipCutscenes(self, wait=(0, 0), detectFreq=(0.3, 1)):
        self.wait(*wait)
        while not self.detect("MasterSkillBtn", 0):
            self.tap("AnyWhere3")
            self.wait(*detectFreq)


    def afterBattle(self):
        while not self.detect("NextBtn", 1):
            self.tap("AnyWhere2")
        self.tap("NextBtn")
        # AgainBtn.detect(30)
        self.wait(0.4, 0.7)
        self.tap("AgainBtn")
        if self.detect("GoldenApple", 3):
            if self.useApple:
                self.tap("GoldenApple")
                self.wait(1, 2)
                self.tap("EatAppleBtn")
                return True
            else:
                return False
        return True




    def initElement(self):
        self.createElement("StagePosition", (960, 276, 1831, 415), None, self.fgoHandler)

        self.createElement("MasterSkillBtn", (1751, 434, 1834, 518), r".\template\masterskillBtn.png",
                           self.fgoHandler)
        self.createElement("MasterSkill1", (1313, 426, 1398, 511), None, self.fgoHandler)
        self.createElement("MasterSkill2", (1445, 430, 1536, 507), None, self.fgoHandler)
        self.createElement("MasterSkill3", (1582, 430, 1670, 507), None, self.fgoHandler)

        self.createElement("Skill_1_1", (77, 829, 154, 914), None, self.fgoHandler)
        self.createElement("Skill_1_2", (211, 829, 288, 914), None, self.fgoHandler)
        self.createElement("Skill_1_3", (338, 829, 419, 914), r".\template\skill1_3_2.png", self.fgoHandler)
        self.createElement("Skill_2_1", (538, 829, 630, 914), None, self.fgoHandler)
        self.createElement("Skill_2_2", (676, 829, 764, 914), None, self.fgoHandler)
        self.createElement("Skill_2_3", (814, 829, 891, 914), None, self.fgoHandler)
        self.createElement("Skill_3_1", (1025, 829, 1102, 914), None, self.fgoHandler)
        self.createElement("Skill_3_2", (1152, 829, 1233, 914), None, self.fgoHandler)
        self.createElement("Skill_3_3", (1290, 829, 1367, 914), None, self.fgoHandler)

        self.createElement("SkillAllyTarget1", (361, 507, 637, 787), None, self.fgoHandler)
        self.createElement("SkillAllyTarget2", (814, 507, 1106, 787), None, self.fgoHandler)
        self.createElement("SkillAllyTarget3", (1306, 507, 1571, 787), None, self.fgoHandler)

        self.createElement("orderChange1", (108, 407, 315, 618), None, self.fgoHandler)
        self.createElement("orderChange2", (403, 407, 614, 618), None, self.fgoHandler)
        self.createElement("orderChange3", (707, 407, 918, 618), None, self.fgoHandler)
        self.createElement("orderChange4", (1000, 407, 1215, 618), None, self.fgoHandler)
        self.createElement("orderChange5", (1300, 407, 1515, 618), None, self.fgoHandler)
        self.createElement("orderChange6", (1600, 407, 1815, 618), None, self.fgoHandler)

        self.createElement("changeBtn", (764, 900, 1164, 975), None, self.fgoHandler)

        self.createElement("Card1", (92, 626, 330, 890), None, self.fgoHandler)
        self.createElement("Card2", (472, 626, 664, 890), None, self.fgoHandler)
        self.createElement("Card3", (852, 626, 1068, 890), None, self.fgoHandler)
        self.createElement("Card4", (1236, 626, 1440, 890), None, self.fgoHandler)
        self.createElement("Card5", (1624, 626, 1839, 890), None, self.fgoHandler)
        self.createElement("SpCard1", (526, 192, 722, 422), None, self.fgoHandler)
        self.createElement("SpCard2", (860, 192, 1060, 422), None, self.fgoHandler)
        self.createElement("SpCard3", (1210, 192, 1405, 422), None, self.fgoHandler)

        self.createElement("StartBtn", (1609, 937, 1878, 1064), r".\template\startBtn.png", self.fgoHandler)
        self.createElement("NextBtn", (1463, 914, 1863, 995), r".\template\nextBtn.png", self.fgoHandler)
        self.createElement("ExitBtn", (507, 814, 814, 883), None, self.fgoHandler)
        self.createElement("AgainBtn", (1097, 814, 1413, 883), r".\template\againBtn.png", self.fgoHandler)
        self.createElement("ATKBtn", (1561, 781, 1829, 1028), r".\template\atkBtn.png", self.fgoHandler)

        self.createElement("PaySenceHead", (880, 392, 1051, 535), r".\template\CAL1.png", self.fgoHandler)
        self.createElement("AnyWhere", (200, 177, 1720, 900), None, self.fgoHandler)
        self.createElement("AnyWhere2", (34, 153, 1406, 1066), None, self.fgoHandler)
        self.createElement("AnyWhere3", (849, 185, 1500, 570), None, self.fgoHandler)
        self.createElement("PleaseTapHint", (730, 909, 1200, 1038), r".\template\PleaseHintBtn.png",
                           self.fgoHandler)

        self.createElement("GoldenApple", (487, 410, 635, 550), r".\template\GoldenApple.png", self.fgoHandler)
        self.createElement("CancelAppleBtn", (517, 824, 800, 865), None, self.fgoHandler)
        self.createElement("EatAppleBtn",(1097, 824, 1399, 883), None, self.fgoHandler)

    @abc.abstractmethod
    def selectAssistant(self):
        pass

    @abc.abstractmethod
    def mainActions(self):
        pass

    def run(self, waitBeforeAssistant=2):
        lastTime = None
        curTime = None
        startTime = time.perf_counter()
        actualTimes = 0
        for i in range(self.runTimes):
            actualTimes = i+1
            if curTime is not None:
                lastTime = curTime
            if lastTime is None:
                lastTime = time.perf_counter()
            curTime = time.perf_counter()

            print("第{}局，共{}局\n上局耗时：{}，总耗时：{}".format(i + 1, self.runTimes,
                                                     time.strftime("%M:%S", time.gmtime(curTime - lastTime)),
                                                     time.strftime("%H:%M:%S", time.gmtime(curTime - startTime))))
            self.wait(waitBeforeAssistant, waitBeforeAssistant)
            self.selectAssistant()
            print("助战选择完毕")
            if (self.detect("StartBtn", 1, detectFreq=0, wait=(0.5, 1))):
                self.tap("StartBtn")
            self.mainActions()
            isContinue = self.afterBattle()
            if not isContinue:
                print("不吃苹果，准备退出……")
                break

        if curTime is not None:
            lastTime = curTime
        if lastTime is None:
            lastTime = time.perf_counter()
        curTime = time.perf_counter()

        print("已完成，共{}局\n上局耗时：{}，总耗时：{}, 平均每局耗时：{}".format(actualTimes,
                                                 time.strftime("%M:%S", time.gmtime(curTime - lastTime)),
                                                 time.strftime("%H:%M:%S", time.gmtime(curTime - startTime)),
                                                 time.strftime("%H:%M:%S", time.gmtime((curTime - startTime) / actualTimes)),
                                                           ))
