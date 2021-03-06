#-------------------------------------------------------------------------------
# Copyright 2017 Cognizant Technology Solutions
# 
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy
# of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations under
# the License.
#-------------------------------------------------------------------------------
'''
Created on Jun 22, 2016

@author: 463188
'''
from dateutil import parser
import datetime
from com.cognizant.devops.platformagents.core.BaseAgent import BaseAgent
class JiraAgent(BaseAgent):
    def process(self):
        userid = self.config.get("userid", '')
        passwd = self.config.get("passwd", '')
        baseUrl = self.config.get("baseUrl", '')
        startFrom = self.config.get("startFrom", '')
        lastUpdated = self.tracking.get("lastupdated", startFrom)
        responseTemplate = self.getResponseTemplate()
        fields = self.extractFields(responseTemplate)
        jiraIssuesUrl = baseUrl+"?jql=updated>='"+lastUpdated+"' ORDER BY updated ASC&maxResults="+str(self.config.get("dataFetchCount", 1000))+'&fields='+fields
        total = 1
        maxResults = 0
        startAt = 0
        updatetimestamp = None
        sprintField = self.config.get("sprintField", None)
        while (startAt + maxResults) < total:
            data = []
            response = self.getResponse(jiraIssuesUrl+'&startAt='+str(startAt + maxResults), 'GET', userid, passwd, None)
            jiraIssues = response["issues"]
            for issue in jiraIssues:
                parsedIssue = self.parseResponse(responseTemplate, issue)
                if sprintField:
                    sprintDetails = issue.get("fields", {}).get(sprintField, None)
                    if sprintDetails:
                        sprintName = []
                        sprintState = []
                        sprintStartDate = []
                        sprintEndDate = []
                        sprintCompletedDate = []
                        activeSprint = []
                        for sprint in sprintDetails:
                            sprintData = {}
                            sprintDetail = sprint.split("[")[1][:-1]
                            sprintPropertieTokens = sprintDetail.split(",")
                            for propertyToken in sprintPropertieTokens:
                                propertyKeyValToken = propertyToken.split("=")
                                sprintData[propertyKeyValToken[0]] = propertyKeyValToken[1]
                            sprintName.append(sprintData.get('name'))
                            sprintState.append(sprintData.get('state'))
                            sprintStartDate.append(sprintData.get('startDate'))
                            sprintEndDate.append(sprintData.get('endDate'))
                            sprintCompletedDate.append(sprintData.get('completeDate'))
                            if sprintData.get('state') == 'ACTIVE':
                                activeSprint.append(sprintData.get('name'))
                        parsedIssue[0]['activeSprint'] = activeSprint
                        parsedIssue[0]['sprintName'] = sprintName
                        parsedIssue[0]['sprintState'] = sprintState
                        parsedIssue[0]['sprintStartDate'] = sprintStartDate
                        parsedIssue[0]['sprintEndDate'] = sprintEndDate
                        parsedIssue[0]['sprintCompletedDate'] = sprintCompletedDate
                data += parsedIssue
            maxResults = response['maxResults']
            total = response['total']
            startAt = response['startAt']
            if len(jiraIssues) > 0:
                updatetimestamp = jiraIssues[len(jiraIssues) - 1]["fields"]["updated"]
                dt = parser.parse(updatetimestamp)
                fromDateTime = dt + datetime.timedelta(minutes=01)
                fromDateTime = fromDateTime.strftime('%Y-%m-%d %H:%M')
                self.tracking["lastupdated"] = fromDateTime
                self.publishToolsData(data)
                self.updateTrackingJson(self.tracking)
            else:
                break            
    
    def extractFields(self, responseTemplate):
        fieldsJson = responseTemplate.get("fields", None)
        fieldsParam = ''
        if fieldsJson:
            for field in fieldsJson:
                fieldsParam += field + ','
        fieldsParam = fieldsParam[:-1]
        if self.config.get("sprintField", None):
            fieldsParam += ','+ self.config.get("sprintField")
        return fieldsParam
            
if __name__ == "__main__":
    JiraAgent()        
