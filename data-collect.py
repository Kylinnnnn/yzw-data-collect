# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

# 创建浏览器对象
browser = webdriver.Chrome()
wantedMasterClass = ["电子信息", "人工智能", "计算机技术", "软件工程"]


class School:
    def __init__(self, code, name, provinceCode, field):
        self.code = code
        self.name = name
        self.provinceCode = provinceCode
        self.field = field
        self.schoolLink = self.generateSchoolLink()
        self.links = []
    #学校详细专业信息的链接
    def generateSchoolLink(self):
        return f"https://yz.chsi.com.cn/zsml/querySchAction.do?ssdm={self.provinceCode}&dwmc={self.name}&mldm=zyxw&mlmc=&yjxkdm=0854&xxfs=1&zymc={self.field}"
    #学校专业详细信息的链接
    def collectMasterInfoLinks(self):
        tempLinks = []
        browser.get(self.schoolLink)
        infoTable = browser.find_element(By.TAG_NAME, "tbody")
        infos = infoTable.find_elements(By.TAG_NAME, "tr")
        for item in infos:
            link = (
                item.find_elements(By.TAG_NAME, "td")[-2]
                .find_element(By.TAG_NAME, "a")
                .get_attribute("href")
            )
            tempLinks.append(link)
        return tempLinks


class finalResult:
    def __init__(
        self, code, name, field, masterDirection, num, foreignCode, proCode1, proCode2
    ):
        self.code = code
        self.name = name
        self.field = field
        self.masterDirection = masterDirection
        self.num = num
        self.foreignCode = foreignCode
        self.proCode1 = proCode1
        self.proCode2 = proCode2

#门类类别
def selectMasterClass():
    mldm = browser.find_element(By.ID, "mldm")
    mldmSelect = Select(mldm)
    #选择专业学位
    mldmSelect.select_by_value("zyxw")

#学科类别
def selectMasterField():
    yjxkdm = browser.find_element(By.ID, "yjxkdm")
    yjxkdmSelect = Select(yjxkdm)
    #根据学科代码选择
    yjxkdmSelect.select_by_value("0854")

#专业名称
def selectMasterName(name):
    zymc = browser.find_element(By.ID, "zymc")
    zymcSelect = Select(zymc)
    #根据专业名称选择
    zymcSelect.select_by_value(name)

#学习方式
def selectStudy():
    xxfs = browser.find_element(By.ID, "xxfs")
    xxfsSelect = Select(xxfs)
    #选择全日制
    xxfsSelect.select_by_value("1")

#获取页面选择的列表
def getPageList():
    return browser.find_elements(By.CLASS_NAME, "lip")

#获取总页数
def getTotalPage():
    list = getPageList()
    item = list[-3]
    return item.find_element(By.TAG_NAME, "a").text

#获取下一页的按钮元素
def getNextPageButton():
    list = getPageList()
    item = list[-2]
    return item.find_element(By.TAG_NAME, "a")

#提交信息
def submit():
    submitButton = browser.find_element(By.NAME, "button")
    submitButton.click()

#获取符合筛选条件的一条学校代号、名称和省份代号、专业名称信息
def getSchoolInfo(el, field):
    schoolInfos = el.find_elements(By.TAG_NAME, "td")
    schoolInfo = schoolInfos[0].find_element(By.TAG_NAME, "a").text
    # [schoolCode, schoolName] = schoolInfo.split(")")
    schoolCode = schoolInfo.split(")")[0]
    schoolName = schoolInfo.split(")")[1]
    schoolCode = schoolCode[1:]
    schoolProvinceCode = schoolInfos[1].text[1:3]
    temp = School(schoolCode, schoolName, schoolProvinceCode, field)
    return temp

#获取一页的符合筛选条件的学校信息
def getSchoolInfosPerPage(field):
    temp = []
    infoTable = browser.find_element(By.CLASS_NAME, "ch-table").find_element(
        By.TAG_NAME, "tbody"
    )
    schools = infoTable.find_elements(By.TAG_NAME, "tr")
    for item in schools:
        temp.append(getSchoolInfo(item, field))
    return temp

#获取所有的符合筛选条件的学校信息
def getSchoolInfos(pageNum, field):
    temp = []
    current = 1
    while current < pageNum:
        nextBtn = getNextPageButton()
        temp.extend(getSchoolInfosPerPage(field))
        current += 1
        nextBtn.click()
    temp.extend(getSchoolInfosPerPage(field))
    return temp

#获取所有意向专业的符合筛选条件的学校信息
def createTargetList():
    targetList = {}
    for i in wantedMasterClass:
        browser.get("https://yz.chsi.com.cn/zsml/queryAction.do")
        browser.implicitly_wait(10)

        selectMasterClass()
        selectMasterField()
        selectStudy()
        selectMasterName(i)

        submit()
        # browser.implicitly_wait(5)
        pageNum = getTotalPage()
        targetList[i] = getSchoolInfos(int(pageNum), i)
        # print(i, ":", pageNum, "页", targetList[i])
    return targetList

#对筛选出的学校信息按各科目考试学科进一步筛选
def dataSelect():
    file1 = open("data1.txt", "w", encoding="utf-8")
    file2 = open("data2.txt", "w", encoding="utf-8")
    schoolLists = createTargetList()
    results = []
    for i in wantedMasterClass:
        for school in schoolLists[i]:
            school.links = school.collectMasterInfoLinks()
            if len(school.links) > 0:
                #所有学校的所有符合条件的专业目录详情链接
                file1.writelines(school.links)
                for link in school.links:
                    browser.get(link)
                    infoTables = browser.find_elements(By.TAG_NAME, "tbody")
                    condition = infoTables[0].find_elements(By.TAG_NAME, "tr")
                    exam = infoTables[1].find_elements(By.TAG_NAME, "td")

                    foreignCode = exam[1].text[1:4]
                    proCode1 = exam[2].text[1:4]
                    #只要英二数二的专业
                    if foreignCode != "204" or proCode1 != "302":
                        continue
                    proCode2 = exam[3].text[1:4]
                    masterDirection = (
                        condition[2].find_elements(By.TAG_NAME, "td")[3].text
                    )
                    num = condition[3].find_elements(By.TAG_NAME, "td")[3].text
                    result = finalResult(
                        school.code,
                        school.name,
                        school.field,
                        masterDirection,
                        num,
                        foreignCode,
                        proCode1,
                        proCode2,
                    )
                    #筛选后
                    file2.write(
                        f"学校代号:{result.code},学校:{result.name},专业:{result.field},研究方向:{result.masterDirection},招生人数:{result.num},外语:{result.foreignCode},专业课1:{result.proCode1},专业课2:{result.proCode2}\n"
                    )
                    results.append(result)
    file1.close()
    file2.close()
    print(results)
    return results


def main():
    # 执行自动化操作
    dataSelect()


if __name__ == "__main__":
    main()
