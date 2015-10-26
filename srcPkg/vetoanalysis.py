import numpy as np
import sys
import bcv
from trigstruct import TrigStruct
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def vetoanalysis(frameCache, chanHName, chanXName, frameTypeChanH, frameTypeChanX, samplFreqH, samplFreqX,
		 highPassCutoff, TriggerHList, TriggerXList, couplingModel,
		 transFnXtoH, analysisStartTime, analysisEndTime,
		 timeShift, outDir, logFid, debugLevel):
  #VETOANALYSIS - Peform veto analysis using instrumental couplings on a set of triggers
  #in the GW channel making use of a set of trigges in the an instrumental channel X and
  #and the transfer function from channel X to the GW channel
  #
  # Usage : vetoanalysis(TriggerHList, TriggerXList, transFnXtoH,numberOfChannels, timeShift)
  # TriggerHList -  A structure containing the start times, and times and central times
  # 		    of the triggers in channel H
  # TriggerXList - A structure containing the strat times, end times and central times of 
  #		   the triggers in channel X
  # TransFnXtoH -  A structure containing the transfer functions (Frequency and 	  		 Amplitude) from channel X to Channel H
  # analysisStartTime - GPS start time lower bound of candidate events
  # analysisEndTime   - GPS end times upper bound of candidate events
  # timeShift	      - The number of seconds by whuch the coincident triggers
  #                     will be time shifted after identification
  
  
  # Sudarshan Ghonge <sudu.ghonge@gmail.com> 
  # Original code written by
  # Aaron B. Pearlman <aaronp1@umbc.edu> and
  # P. Ajith <ajith.icts.res.in>
  
  #maximum number of allowed coincidences
  maxNumCoinc = len(TriggerHList.centralTime)*len(TriggerXList.centralTime)
  
  #Time window for identifying coincidences between channel H and X
  COINC_TIME_WINDOW = 0.5
  
  #Maximum length of one data segment used for the analysis
  MAX_LENGTH_DATA_SEG = 64
  
  ################Ask Ajith what this means#
  segLength = 3600
  
  uniqueArgument = 'nonunique'
  
  logFid.write( 'LOG: Finding coincidences... Num trigs H = %d, Num trigs X = %d\n'\
    %(len(TriggerHList.centralTime), len(TriggerXList.centralTime)))
  
  [coincTrigH, coincTrigX] = bcv.mcoinc(maxNumCoinc, TriggerHList.centralTime, TriggerXList.centralTime + timeShift, COINC_TIME_WINDOW, segLength, uniqueArgument)
  
  #print 'coincTrigH', coincTrigH
  trigHCentralTimeVec = TriggerHList.centralTime[coincTrigH]
  trigXCentralTimeVec = TriggerXList.centralTime[coincTrigX]
  
  trigHStartTimeVec = TriggerHList.startTime[coincTrigH]
  trigXStartTimeVec = TriggerXList.startTime[coincTrigX]
  
  trigHEndTimeVec = TriggerHList.endTime[coincTrigH]
  trigXEndTimeVec = TriggerXList.endTime[coincTrigX]
  
  trigHCentFreqVec = TriggerHList.centralFrequency[coincTrigH]
  trigXCentFreqVec = TriggerXList.centralFrequency[coincTrigX]
  
  trigHSignificVec = TriggerHList.triggerSignificance[coincTrigH]
  trigXSignificVec = TriggerXList.triggerSignificance[coincTrigX]
  
  trigHDurationVec = trigHEndTimeVec - trigHStartTimeVec
  trigXDurationVec = trigXEndTimeVec - trigXStartTimeVec
  
  del TriggerHList, TriggerXList
  
  ##Read Data Segments Using a Time-Window Around Coi-incident Triggers
  
  ##Check if the sample frequencies of Channel H X are the same. If not, throw error
  
  #if(samplFreqH!=samplFreqX):
    #sys.exit('Error: samplFreqH DOES NOT equal samplFreqX')
  #else:
    #samplFreq = samplFreqH
  samplFreq = samplFreqH
  # Apply time shift to the X/Y data. In case of bilinear coupling, there are multiple
  # channels (X and Y); thus a vector of length 2 or more
  
  if(couplingModel=='linear'):
    timeShiftX = timeShift
  elif(couplingModel=='bilinear'):
    timeShiftX = np.zeros(len(chanXName))
    for iX in range(len(chanXName)):
      timeShiftX[iX] = timeShift
  #Check number of triggers in channel H that are coincident in channel X (coincTrigH) 
  #is the same the number of triggers in Channel X that are coincident in Channel H
  #(coincTrigX)
  if(len(coincTrigH)==len(coincTrigX) & len(coincTrigH)>0):
    
    #Read data for timeShift from frameCache
    logFid.write('LOG: Performing veto analysis for time shift %d..\n' %(timeShift))
    logFid.write('LOG: Number of coincidences : %d...\n' %(len(coincTrigH)))
    
    
    #Initializing empty lists to store the post analysis data
    timeShiftVec = []
    rHPMat = []
    rMaxHPMat = []
    meanYMat = []
    varYMat = []
    varYMat = []
    minYMat = []
    maxYMat = []
    mindYMat = []
    maxdYMat = []
    meandYMat = []
    trigHAnalysdCentTimeVec = []
    trigXAnalysdCentTimeVec = []
    trigHAnalysdCentFreqVec = []
    trigXAnalysdCentFreqVec = []
    trigHAnalysdSignificVec = []
    trigXAnalysdSignificVec = []
    trigHAnalysdDurationVec = []
    trigXAnalysdDurationVec = []
    
    
    #testId = open('test_' + '%d'%(analysisStartTime) + '.dat', 'w+')
    #np.savetxt(testId, trigHCentralTimeVec)
    #testId.close()
    #outFileString = '/corrstat_timeshift%d_seg%d-%d.dat'%(timeShift, analysisStartTime, analysisEndTime)
    #outFileName = outDir[iP] + '/' + outFileString
    #outFid = open(outFileName, 'w+')
    
    if(debugLevel>=2):
      import os
      debugPlotsFolder =  'debug_plots/' + 'timeshift%d'
      debugPlotsDir = outDir[0] +  debugPlotsFolder
      os.system('mkdir -p %s'%(debugPlotsDir))
      
    for coincIndex in range(len(coincTrigH)):
      trigHCentTime = trigHCentralTimeVec[coincIndex]
      trigXCentTime = trigXCentralTimeVec[coincIndex]
      
      trigHStartTime = trigHStartTimeVec[coincIndex]
      trigXStartTime = trigXStartTimeVec[coincIndex]
      
      trigHEndTime = trigHEndTimeVec[coincIndex]
      trigXEndTime = trigXEndTimeVec[coincIndex]
      
      trigHCentFreq = trigHCentFreqVec[coincIndex]
      trigXCentFreq = trigXCentFreqVec[coincIndex]
      
      trigHSignific = trigHSignificVec[coincIndex]
      trigXSignific = trigXSignificVec[coincIndex]
      
      trigHDuration = trigHEndTime - trigHStartTime
      trigXDuration = trigXEndTime - trigXStartTime
      
      # Find the segent of data used for analysis      
      segStartTime = min(trigHStartTime, trigXStartTime+timeShift)
      segEndTime   = max(trigHEndTime, trigXEndTime + timeShift)
      meanTrigCentTime = (segStartTime + segEndTime)/2.0
      totalDuration = segEndTime - segStartTime
      
      # Calculate the total number of samples, rounded to the closest integer
      # power of 2 
      totalNumberSamples = bcv.roundtopowertwo(totalDuration*samplFreq, 1024.0)
      
      # Calculate the length of the data segment used for veto analysis
      segmentDuration = totalNumberSamples / samplFreq
      
      # Find the start and end times of a samll segment of dara that we want to
      # analyse
      segStartTime = meanTrigCentTime - segmentDuration / 2.0
      segEndTime = meanTrigCentTime + segmentDuration/2.0
      
      # Round the start and end times of a small segment of dara that we want to
      # analyse to an integer of gps time.
      # IMPORTANT NOTE: One second of data in the beginning is used to train the high
      # pass filter and hecne should not be used for the analysis (this explains 
      # the "floor(segStartTime) - 1" below).
      
      
      bcvreadStartTime = np.floor(segStartTime) - 1
      bcvreadEndTime = np.ceil(segEndTime) + 1
      
      if (debugLevel >=2):
	#print values of different variables
	bcv.printvar('--- Analysis Window ---',''
		 ,'analysisStartTime',analysisStartTime, 
		 'analysisEndTime', analysisEndTime,
                'wreadStartTime', bcvreadStartTime, 
                'wreadEndTime', bcvreadEndTime, 
                'segStartTime', segStartTime, 
                'segEndTime', segEndTime, 
                '--- Trigger Parameters ---','',
                'trigHStartTime', trigHStartTime, 
                'trigXStartTime', trigXStartTime, 
                'trigHEndTime', trigHEndTime, 
                'trigXEndTime', trigXEndTime, 
                'trigHCentTime', trigHCentTime, 
                'trigXCentTime', trigXCentTime, 
                'trigHCentFreq', trigHCentFreq, 
                'trigXCentFreq', trigXCentFreq, 
                'trigHSignific', trigHSignific, 
                'trigXSignific', trigXSignific, 
                '--- Veto Analysis Parameters ---', '', 
                'meanTrigCentTime',meanTrigCentTime,
                'totalDuration', totalDuration)
	
      #Check if data is sensible	
      if((segStartTime<analysisStartTime) | (segEndTime>analysisEndTime)): 
	logFid.write('ERROR: segment startTime (%d)/stopTime (%d) is outside the analysis interval [%d, %d]\n'%( bcvreadEndTime, bcvreadEndTime, analysisStartTime, analysisEndTime))
      elif(bcvreadEndTime-bcvreadStartTime>MAX_LENGTH_DATA_SEG):
	logFid.write('ERROR: Segment length %f is larger than the allowed max length of %f..\n' 
	  %(bcvreadEndTime-bcvreadStartTime, MAX_LENGTH_DATA_SEG))
      else:
	#Read the segment for channel H and channel X
	[dataH, samplFreqH] = bcv.readData(frameCache, chanHName, frameTypeChanH, bcvreadStartTime,
				    bcvreadEndTime, [0], debugLevel)
	
	[dataX, samplFreqX] = bcv.readData(frameCache, chanXName, frameTypeChanX, bcvreadStartTime,
				    bcvreadEndTime, timeShiftX, debugLevel)
	#Check for a read error in the channel H data.
	if(not all(samplFreqH)):
	  logFid.write('ERROR: Cannot load frame data for channel H...\n')
	  logFid.write('ERROR: Channel H - bcvreadStartTime: %f bcvreadEndTime: %f\n'%( bcvreadStartTime, bcvreadEndTime))
	elif(not all(samplFreqX)):
	  logFid.write('ERROR: Cannot load frame data for channel X\n')
	  logFid.write('ERROR: Channel X -  bcvreadStartTime: %f bcvreadEndTime: %f..\n'%(bcvreadEndTime, bcvreadEndTime ))
	  
	else:
	  #del timeH, timeX
	  
	  timeH = np.arange(bcvreadEndTime, bcvreadEndTime - 1.0/samplFreqH, 1.0/samplFreqH)
	  
	  timeX = []
	  for iX in range(0, len(samplFreqX)):
	    timeX.append(np.arange(bcvreadEndTime - timeShift, bcvreadEndTime -timeShift - 1.0/samplFreqX[iX], 1.0/samplFreqX[iX]))
	  
	  timeX = np.asarray(timeX)
	  
	    
	    
	  # If sampling frequency is different from the one specified,
	  # resample the data
	  if(samplFreqH != samplFreq):
	    dataH = np.asarray([bcv.resample2(dataH[0], samplFreqH[0], samplFreq)])
	  if(not all(samplFreqX==samplFreq)):
	    index = np.where(samplFreqX!=samplFreq)[0]
	    for iDs in index:
	      dataX[iDs] = bcv.resample2(dataX[iDs], samplFreqX[iDs], samplFreq)
	    
	  del timeH, timeX
	  timeH = np.arange(bcvreadStartTime, bcvreadEndTime - 1.0/samplFreq, 1.0/samplFreq)
	  timeX = np.arange(bcvreadStartTime-timeShift, bcvreadEndTime-timeShift -1.0/samplFreq, 1.0/samplFreq)
	  
	  
	  # In case of bilinear coupling multiply the X and Y channels
	  # to form a pseudo channel (which a combination of X and Y)
	  # Also compute some parameters descrining the slow channels(s)
	  # and store them in vectors.
	  if(couplingModel=='bilinear'):
	    segIdx = np.intersect1d(np.where(timeX + timeShift>=segStartTime)[0], np.where(timeX+timeShift<segEndTime)[0])
	    
	    meanY = np.mean(dataX[1][segIdx])
	    varY  = np.var(dataX[1][segIdx])
	    maxY  = np.max(dataX[1][segIdx])
	    minY  = np.min(dataX[1][segIdx])
	    maxYMat.append(maxY)
	    meanYMat.append(meanY)
	    varYMat.append(varY)
	    minYMat.append(minY)
	    #mindY = np.min(np.diff(dataX[iChan][segIdx]))
	    #maxdY = np.max(np.diff(dataX[iChan][segIdx]))
	    #meandY= np.mean(np.diff(dataX[iChan][segIdx]))
	    
	    dataP = np.asarray([dataX[0]*dataX[1]])
	    
	    del dataX
	    dataX = dataP
	    del dataP
	  else:
	    meanY = 0
	    varY = 0
	    maxY = 0
	    minY = 0
	    #mindY = 0
	    #maxdY = 0
	    #meandY = 0
	  if(highPassCutoff>0):
	    dataH = bcv.highpass(dataH, samplFreq, highPassCutoff)
	    dataX = bcv.highpass(dataX, samplFreq, highPassCutoff)
          
          if (debugLevel>=2):
	    if((trigHSignific>=15.0) & (trigXSignific>=15.0)):
	      props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
	      
	      # Plot time series data for Channel X
	      plt.figure()
	      if(len(dataX)>1):
		plt.subplot(3, 1, 1)
	      else:
		plt.subplot(2, 1, 1)
	      plt.plot(timeX[0] - min(timeX[0]), dataX[0], label='x(t)')
	      ax = plt.gca()
	      bot, top = ax.get_ylim()	      
	      ax.axvline(trigXCentTime, color='r', linestyle='--')
	      ax.text(trigXCentTime-min(timeX[0]),top/10.0, '%f'%(trigXCentTime-min(timeX[0])) )
	      ax.text(0.3, 0.9, 'Duration=%f\nSignificance=%f\n'%(trigXDuration,trigXSignific ), ransform=ax.transAxes, fontsize=14,
	       verticalalignment='top', bbox=props)
	      plt.xlabel('t[sec] since')
	      plt.ylabel('Time series data: ' + chanXName[0])
	      plt.legend()
	      
	      #Plot time series data for channel H
	      if(len(dataX)>1):
		plt.subplot(3, 1, 2)
	      else:
		plt.subplot(2, 1, 2)	      
	      plt.plot(timeH[0] - min(timeH[0]), dataH[0], label='h(t)')
	      ax = plt.gca()
	      bot, top = ax.get_ylim()	      
	      ax.axvline(trigHCentTime, color='r', linestyle='--')
	      ax.text(trigHCentTime-min(timeH[0]),top/10.0, '%f'%(trigHCentTime-min(timeH[0])) )
	      ax.text(0.3, 0.9, 'Duration=%f\nSignificance=%f\n'%(trigHDuration,trigHSignific ), ransform=ax.transAxes, fontsize=14,
	       verticalalignment='top', bbox=props)	      
	      plt.xlabel('t[sec] since')
	      plt.ylabel('Time series data: ' + chanHName[0])
	      plt.legend()
	      
	      # Plot time series data for channel Y
	      if(len(dataX)>1):
		plt.subplot(3, 1, 3)
		plt.plot(timeX[1] - min(timeX[1]), dataX[1], label='y(t)')
		plt.xlabel('t[sec] since')
		plt.ylabel('Time series data: ' + chanXName[1])
		plt.legend()
	      plt.savefig(debugPlotsDir + '/CentXTime_%f_CentHTime_%f_TimeSeries.png'%(trigXCentTime, trigHCentTime))
	      plt.close()
	      
	      # Plot spectrogram of X data and Y data
	      plt.figure()
	      
	      plt.subplot(2,1,1)
	      plt.specgram(dataX[0], noverlap=0, Fs=samplFreq)
	      plt.xlabel('t[sec] since')
	      plt.ylabel('Fourier Frequencies')
	      plt.title('channel X specgram')
	      ax = gca()
	      bot, top = ax.get_ylim()
	      left, right = ax.get_xlim()
	      ax.axhline(trigXCentFreq, color='w',linestyle='--', linewidth=3 )
	      ax.text(right/20.0, trigXCentFreq, '%f'%(trigXCentFreq))
	      plt.colormap()
	      
	      plt.subplot(2,1,2)
	      plt.specgram(dataH[0], noverlap=0, Fs=samplFreq)
	      plt.xlabel('t[sec] since')
	      plt.ylabel('Fourier Frequencies')
	      plt.title('channel H specgram')	      
	      ax = gca()
	      bot, top = ax.get_ylim()
	      left, right = ax.get_xlim()
	      ax.axhline(trigXCentFreq, color='w',linestyle='--', linewidth=3 )
	      ax.text(right/20.0, trigHCentFreq, '%f'%(trigHCentFreq))
	      plt.colormap()
	      plt.savefig(debugPlotsDir + '/CentXTime_%f_CentHTime_%f_Specgram.png'%(trigXCentTime, trigHCentTime))
	      plt.close()
	      
  
	  
	  
	  [rHP, rMaxHP] = bcv.bilinearCouplingCoeff(dataH[0],
					     dataX, timeH, timeX, segStartTime,
					     segEndTime,timeShift, samplFreq, logFid,
					    debugLevel)
	  
	  timeShiftVec.append(timeShift)
          rHPMat.append(rHP)
	  rMaxHPMat.append(rMaxHP)
	  #mindYMat.append(mindY)
	  #maxdYMat.append(maxdY)
	  #meandYMat.append(meandY)
	  
	  trigHAnalysdCentTimeVec.append(trigHCentTime)
	  trigXAnalysdCentTimeVec.append(trigXCentTime)
	  trigHAnalysdCentFreqVec.append(trigHCentFreq)
	  trigXAnalysdCentFreqVec.append(trigXCentFreq)
	  trigHAnalysdSignificVec.append(trigHSignific)
	  trigXAnalysdSignificVec.append(trigXSignific)
	  trigHAnalysdDurationVec.append(trigHDuration)
	  trigXAnalysdDurationVec.append(trigXDuration)
	  
    
    
    timeShiftVec = np.asarray(timeShiftVec)
    rHPMat = np.asarray(rHPMat)
    rMaxHPMat = np.asarray(rMaxHPMat)
    meanYMat = np.asarray(meanYMat)
    varYMat = np.asarray(varYMat)
    minYMat = np.asarray(minYMat)
    #mindYMat = np.asarray(mindYMat)
    #maxYMat = np.asarray(maxYMat)
    #maxdYMat = np.asarray(maxdYMat)
    #meandYMat = np.asarray(meandYMat)
    
    trigHAnalysdCentTimeVec = np.asarray(trigHAnalysdCentTimeVec)
    trigXAnalysdCentTimeVec = np.asarray(trigXAnalysdCentTimeVec)
    trigHAnalysdCentFreqVec = np.asarray(trigHAnalysdCentFreqVec)
    trigXAnalysdCentFreqVec = np.asarray(trigXAnalysdCentFreqVec)
    trigHAnalysdSignificVec = np.asarray(trigHAnalysdSignificVec)
    trigXAnalysdSignificVec = np.asarray(trigXAnalysdSignificVec)
    trigHAnalysdDurationVec = np.asarray(trigHAnalysdDurationVec)
    trigXAnalysdDurationVec = np.asarray(trigXAnalysdDurationVec)
    
    # combine the correlation from multiple pseudochannels
    # assmuing that all pseudochannels are orthogonal
    # (not strictly true)
    rHPCombVec = np.sqrt(np.sum(rHPMat**2.0, axis=1)) 
    rMaxHPCombVec = np.sqrt(np.sum(rMaxHPMat**2.0, axis=1))
    outFileString = '/corrstat_timeshift%d_seg%d-%d.dat'%(timeShift, analysisStartTime, analysisEndTime)
    
    #save the analysis results from each pseudochannel in a separate file
    for iP in range(0, len(outDir)):
      outFileName = outDir[iP] + '/' + outFileString
      
      resultsMatrix = np.asarray([timeShiftVec, rHPMat[:, iP], rMaxHPMat[:, iP],
				  trigHAnalysdCentTimeVec, trigXAnalysdCentTimeVec, trigHAnalysdCentFreqVec, trigXAnalysdCentFreqVec, trigHAnalysdSignificVec,  trigXAnalysdSignificVec, trigHAnalysdDurationVec,  trigXAnalysdDurationVec, meanYMat, varYMat, 
				  maxYMat, minYMat], dtype=np.float64).transpose()
      resultsMatrix = resultsMatrix[resultsMatrix[:,5 ].argsort()]
      
      np.savetxt(outFileName, resultsMatrix, delimiter = ' ', fmt = '%f')
      
      del resultsMatrix, timeShiftVec, rHPMat, rMaxHPMat, rHPCombVec, rMaxHPCombVec
      del trigHAnalysdCentTimeVec, trigXAnalysdCentTimeVec, trigHAnalysdCentFreqVec
      del trigXAnalysdCentFreqVec, trigHAnalysdSignificVec, trigXAnalysdSignificVec
      del trigHAnalysdDurationVec, trigXAnalysdDurationVec
      del meanYMat, varYMat, maxYMat, minYMat, mindYMat, maxdYMat, meandYMat
  
  else:
    logFid.write('WARNING: No coincident triggers found for timeshift = %d..\n' %(timeShift))
  
  
  
  
  