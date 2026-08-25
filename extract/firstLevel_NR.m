%% First level analysis of reading tasks
%triggers in task:  10 = sentence start, 11 = sentence end,
%                   12 = ctrl_sentence start, 13 = ctrl sentence end,
%                   15 = answer given (to ctrl_question)

clc
clear all;

% ############ pathsettings #####################
addpath(genpath('C:\Users\Marius\Documents\toolboxes\eeglab14_1_1b'))
addpath(genpath([pwd filesep 'lib'])); % add  lib folder (folder has to be in the same location as script)

% specify the folder with the preprocessed data:
prepocFold='C:\Users\Marius\Downloads\NLP\NR';
% ################################################

status=mkdir([preprocFold filesep 'firstLevelResults']);

% Some variables:
nChans=105;
subjects={'ZAB','ZDM','ZDN','ZGW','ZJM','ZJN','ZKB','ZKH','ZKW','ZMG','ZPH'};
doSanityPlot=0; % plot fixations and wordbounds to check ET data sanity for EACH sentence

for sj=1:length(subjects)
    
    clearvars -except prepocFold subjects sj doSanityPlot nChans
    subject=subjects{sj};
    
    
    fold=[prepocFold filesep subject];
    foldpreproc=fold; %if preprocessed data is in the same directory
    
    %add lib folder
    
    
    %taskspecific:
    sentences_per_file=50;
    nFiles=6;
    
    %% load in sentences, wordbounds, EEG and ET files of subject
    
    %load sentences:

    load([prepocFold filesep 'sentencesNR.mat']);
    sentences(1:5)=[]; %delete first 5 sentences which are used for practice run
    
    %load wordbounds:
    c=load([fold filesep 'wordbounds_NR_' subject '.mat']);
    bounds=c.wordbounds;
    bounds=calcNewBoundsFunc(bounds);
    
    %% load EEG and Eyetracker (ET) files
    
    d=dir(fold);
    
    %############################### ET Files ###############################
    
    % xxxxxxx find missing ET files: xxxxxxx
    index_et = find(contains({d.name},'corrected_ET.mat') & contains({d.name},'_NR'));
    
    prevNr_et=0;
    missing_et=[];
    
    for i=1:size(index_et,2)
        
        currname=d(index_et(i)).name;
        nr_et=str2num(currname(end-17));
        
        if not(nr_et==prevNr_et+1)
            for ii=prevNr_et+1:nr_et-1
                missing_et=[missing_et ii];
            end
            prevNr_et=nr_et;
        else
            prevNr_et=nr_et;
        end
    end
    %last files missing?
    if nr_et <nFiles
        for ii=nr_et+1:nFiles
            missing_et=[missing_et ii];
        end
    end
    % xxxxxxx xxxxxx xxxxxx xxxxxxxxx
    
    % define filenames for available eyetracking files:
    cntET=1;
    for i=1:size(index_et,2)
        
        currname=d(index_et(i)).name;
        nr_et=str2num(currname(end-17));
        eval(['et' num2str(nr_et) '= [ fold filesep d(' num2str(index_et(i)) ').name]']);
        cntET=cntET+1;
        
    end
    
    % #####################################################################
    
    % ############################## EEG Files ############################
    
    d2=dir(foldpreproc);
    cntEEG=1;
    
    % xxxxxx find missing eeg files: xxxxxxx
    index = find(contains({d2.name},'_EEG.mat') & contains({d2.name},'_NR'));
    
    missing=[];
    names=d2(index);
    
    %check each file-number (here 1-6)
    for i=1:nFiles
        %does any of the names conatin this number?
        found=0;
        for ii=1:size(names,1)
            if contains(names(ii).name,['NR' num2str(i)])
                found=1;
            end
        end
        if not(found)
            missing=[missing i];
        end
    end
    % xxxxxxx xxxxxxx xxxxxxx xxxxxxx
    
    % load available eeg files
    cntEEG=1;
    for i=1:length(index)
        
        currname=d2(index(i)).name;
        nr=str2num(currname(end-8));
        disp(['loading eeg file: ' d2(index(i)).name ' as eeg' num2str(nr)]);
        eval(['eeg' num2str(nr) '=load([ foldpreproc filesep d2(' num2str(index(i)) ').name])']);
        cntEEG=cntEEG+1;
        
    end
    
    
    
    %% insert eyetracker data into eeg data as additional channels, also import
    %% eyeevents!
    
    % define triggers for merging:
    for i=1:nFiles
        if any(i==missing) || any(i==missing_et)
            %do nothing, just skip
        else
            if i==1
                ev1=12;
                ev2=11;
            elseif i==2
                ev1=12;
                ev2=11;
            elseif i==3
                ev1=10;
                ev2=11;
            elseif i==4
                ev1=10;
                ev2=11;
            elseif i==5
                ev1=10;
                ev2=13;
            elseif i==6
                ev1=10;
                ev2=11;
            end
            
            %merge the eeg and eyetracker datasets using the two first triggers
            evalc(['tmp_et=load(et' num2str(i) ')']);
            if(isempty(tmp_et.eyeevent.fixations.data))
                disp(['Skipping file nr ' num2str(i) ', no fixations in ET data - CHECK PREPARE ET SCRIPT']);
            else
                eval([' disp([''merging eeg''  num2str(i) '' with '' et' num2str(i) '])']);
                evalc(['eeg'  num2str(i) '=pop_importeyetracker(eeg'  num2str(i) '.EEG, et'  num2str(i) ',[ev1 ev2],[1:4], {''TIME'' ''L_GAZE_X'' ''L_GAZE_Y'' ''L_AREA''},1,1,0,0,4)']);
                
            end
        end
    end
    
    
    %merge the split datasets
    firstset=1;
    FullEEG=[];
    for i=1:nFiles
        if not(any(i==missing) || any(i==missing_et))
            if firstset
                evalc(['FullEEG=eeg' num2str(i)]);
                firstset=0;
            else
                disp(['Merging file nr ' num2str(i) ]);
                evalc(['FullEEG=pop_mergeset(FullEEG,eeg' num2str(i) ')']);
            end
        end
    end
    
    
    %% Filter to different Frequencybands:
    
    %theta1 4�6;
    %theta2 6�8;
    %alpha1: 8�10;
    %alpha2: 10�13;
    %beta1 : 13�18;
    %beta2 : 18�30;
    %Gamma1: 30-40;
    %Gamma2: 40-50;
    
    
    %frequency definitions:
    
    t1_l=4;t1_h=6; t2_l=6.5;t2_h=8;
    a1_l=8.5;a1_h=10; a2_l=10.5;a2_h=13;
    b1_l=13.5;b1_h=18; b2_l=18.5;b2_h=30;
    g1_l=30.5;g1_h=40; g2_l=40.5;g2_h=49.5;
    
    %filter and save the data (for hilbert transform later):
    tmp= pop_eegfiltnew(FullEEG,t1_l,t1_h);
    FullEEG.data_t1=tmp.data;
    
    tmp= pop_eegfiltnew(FullEEG,t2_l,t2_h);
    FullEEG.data_t2=tmp.data;
    
    tmp= pop_eegfiltnew(FullEEG,a1_l,a1_h);
    FullEEG.data_a1=tmp.data;
    
    tmp= pop_eegfiltnew(FullEEG,a2_l,a2_h);
    FullEEG.data_a2=tmp.data;
    
    tmp= pop_eegfiltnew(FullEEG,b1_l,b1_h);
    FullEEG.data_b1=tmp.data;
    
    tmp= pop_eegfiltnew(FullEEG,b2_l,b2_h);
    FullEEG.data_b2=tmp.data;
    
    tmp= pop_eegfiltnew(FullEEG,g1_l,g1_h);
    FullEEG.data_g1=tmp.data;
    
    tmp= pop_eegfiltnew(FullEEG,g2_l,g2_h);
    FullEEG.data_g2=tmp.data;
    
    clear tmp;
    
    %% extract data during all fixations:
    %find out which files to ignore (missing either in ET or in EEG):
    
    missing_general=[];
    for i=1:nFiles
        if any(i==missing) || any(i==missing_et)
            missing_general=[missing_general i];
        end
    end
    
    %delete wordbounds and sentences which have no matching eeg or et data:
    if size(bounds,2)>300
        bounds(301:end)=[];
    end
    delete=[];
    for i=1:nFiles
        if any(i==missing_general)
            delete=[delete (1+(i-1)*50):((1+(i-1)*50)+sentences_per_file-1)];
        end
    end
    bounds(delete)=[];
    sentences(delete)=[];
    
    
    
    %extract all fixations which are inbetween start- and stop-triggers of
    %sentences:
    
    allFixations=[];
    allFixations.x=[];
    allFixations.y=[];
    cntSent=0;
    nSentExcluded=0;
 
    for i=1:length(FullEEG.event)
        %if sentence-start-trigger found
        if strcmp( FullEEG.event(i).type, '10  ') || strcmp( FullEEG.event(i).type, '12  ')
            
            cntSent=cntSent+1;
            sentStart(cntSent)=FullEEG.event(i).latency;
            cntFix=0;
            ii=i;
            
            % while not reached end-trigger of the current sentence:
            while not(strcmp( FullEEG.event(ii).type, '11  ') || strcmp( FullEEG.event(ii).type, '13  '))
                ii=ii+1;
                
                %extract relevant fixation data:
                if contains(FullEEG.event(ii).type,'fixation')
                    
                    cntFix=cntFix+1;
                    allFixations(cntSent).x(cntFix)=FullEEG.event(ii).fix_avgpos_x;
                    allFixations(cntSent).y(cntFix)=FullEEG.event(ii).fix_avgpos_y;
                    % GET FULL DURATION
                    allFixations(cntSent).duration(cntFix)=FullEEG.event(ii).duration;
                    allFixations(cntSent).pupilsize(cntFix)=FullEEG.event(ii).fix_avgpupilsize;
                    startEEG=FullEEG.event(ii).latency;
                    stopEEG=startEEG+FullEEG.event(ii).duration;
                    allFixations(cntSent).eegStart(cntFix)=startEEG;
                    allFixations(cntSent).eegStop(cntFix)=stopEEG;
                    
                end
            end
            sentStop(cntSent)=FullEEG.event(ii).latency;
            
            %Plot (check if bounds match fixationdata)
            if doSanityPlot
                bo_2=bounds{cntSent};
                clf;
                hold on;
                for ij=1:size(bo_2,1)
                    rectangle('Position',[bo_2(ij,1) (bo_2(ij,2)) (bo_2(ij,3)-bo_2(ij,1)) (bo_2(ij,4)-(bo_2(ij,2)))]);
                end
                scatter(allFixations(cntSent).x,allFixations(cntSent).y);
                hold off
                title(num2str(cntSent));
                k=waitforbuttonpress;
            end
            
            %check if there is bad data within a sentence, exclude!
            if max(max(FullEEG.data(1:105,sentStart(cntSent):sentStop(cntSent))))>90 ...
                    || min(min(FullEEG.data(1:105,sentStart(cntSent):sentStop(cntSent))))<-90
                nSentExcluded=nSentExcluded+1;
                sentStop(cntSent)=0;
            end
            
        end
    end
    
    
    %% check which fixations are within wordbounds, extract matching data:
    
    y_offset=0; %number of pixels above and below words which still count as fixation on the word
    nExcluded=0;
    nTrials=0;
    for i=1:length(allFixations)
        currBounds=bounds{i};
        
        tmp_wordFixations=[];
        tmp_wordFixationsDuration=[];
        tmp_wordFixationPupil=[];
        tmp_wordEEGStart=[];
        tmp_wordEEGStop=[];
        
        %loop through all fixations wihtin the current sentence:
        for ii =1:length(allFixations(i).x)
            
            %check if current fixation is within bounds of a word
            for w=1:size(currBounds,1)
                if allFixations(i).x(ii) >= currBounds(w,1) &&  allFixations(i).x(ii) <= currBounds(w,3) ...
                        && allFixations(i).y(ii) >= (currBounds(w,2)- y_offset) && allFixations(i).y(ii)  <= (currBounds(w,4)+(y_offset*2))
                    
                    %exclude WordFixations which are shorter than 50 samples (=100ms)
                    if allFixations(i).duration(ii)>=50
                        %save the word which was fixated
                        tmp_wordFixations(end+1)=w;
                        tmp_wordFixationsDuration(end+1)= allFixations(i).duration(ii);
                        tmp_wordFixationPupil(end+1)=allFixations(i).pupilsize(ii);
                        
                        %check if EEG data during this fixation is ok
                        %(thresholding +- 90 microvolt)
                        tmp_eegdat=FullEEG.data(:,allFixations(i).eegStart(ii):allFixations(i).eegStop(ii)); nTrials=nTrials+1;
                        if max(max(tmp_eegdat(1:105,:)))>90 || min(min(tmp_eegdat(1:105,:)))<-90
                            nExcluded=nExcluded+1;
                            tmp_wordEEGStart(end+1)=allFixations(i).eegStart(ii);
                            tmp_wordEEGStop(end+1)=0;
                        else
                            tmp_wordEEGStart(end+1)=allFixations(i).eegStart(ii);
                            tmp_wordEEGStop(end+1)=allFixations(i).eegStop(ii);
                        end
                    end
                end
            end
        end
        wordFixations{i}=tmp_wordFixations;
        
        allFixations(i).words=tmp_wordFixations;
        allFixations(i).word_fixationDuration=tmp_wordFixationsDuration;
        allFixations(i).word_avgPupilsize=tmp_wordFixationPupil;
        allFixations(i).word_EEGStart=tmp_wordEEGStart;
        allFixations(i).word_EEGStop=tmp_wordEEGStop;
        
        
        if not(isempty(tmp_wordFixations))
            for ii=1:length(tmp_wordFixations)
                sent=sentences{i};
                sent= strsplit(sent,' ');
            end
        end
        
    end
    
    %% get theta alpha and beta power during all word-fixations:
    
    for i=1:length(allFixations)
        
        tmp_mean_t1=[];tmp_mean_t2=[];
        tmp_mean_a1=[];tmp_mean_a2=[];
        tmp_mean_b1=[];tmp_mean_b2=[];
        tmp_mean_g1=[];tmp_mean_g2=[];
        
        for ii=1:length(allFixations(i).word_EEGStart)
            currEEGStart=allFixations(i).word_EEGStart(ii);
            currEEGStop=allFixations(i).word_EEGStop(ii);
            
           
            if not(currEEGStop==0)
                %theta:
                tmp_mean_t1(ii,:)= mean(abs(hilbert(FullEEG.data_t1(1:nChans,currEEGStart:currEEGStop)')'),2)';
                tmp_mean_t2(ii,:)= mean(abs(hilbert(FullEEG.data_t2(1:nChans,currEEGStart:currEEGStop)')'),2)';
                %alpha:
                tmp_mean_a1(ii,:)= mean(abs(hilbert(FullEEG.data_a1(1:nChans,currEEGStart:currEEGStop)')'),2)';
                tmp_mean_a2(ii,:)= mean(abs(hilbert(FullEEG.data_a2(1:nChans,currEEGStart:currEEGStop)')'),2)';
                %beta
                tmp_mean_b1(ii,:)= mean(abs(hilbert(FullEEG.data_b1(1:nChans,currEEGStart:currEEGStop)')'),2)';
                tmp_mean_b2(ii,:)= mean(abs(hilbert(FullEEG.data_b2(1:nChans,currEEGStart:currEEGStop)')'),2)';
                %gamma
                tmp_mean_g1(ii,:)= mean(abs(hilbert(FullEEG.data_g1(1:nChans,currEEGStart:currEEGStop)')'),2)';
                tmp_mean_g2(ii,:)= mean(abs(hilbert(FullEEG.data_g2(1:nChans,currEEGStart:currEEGStop)')'),2)';
            else
                tmp_mean_t1(ii,:)= repmat(NaN,1,105);
                tmp_mean_t2(ii,:)= repmat(NaN,1,105);
                %alpha:
                tmp_mean_a1(ii,:)= repmat(NaN,1,105);
                tmp_mean_a2(ii,:)= repmat(NaN,1,105);
                %beta
                tmp_mean_b1(ii,:)= repmat(NaN,1,105);
                tmp_mean_b2(ii,:)= repmat(NaN,1,105);
                %gamma
                tmp_mean_g1(ii,:)= repmat(NaN,1,105);
                tmp_mean_g2(ii,:)= repmat(NaN,1,105);
            end
        end
        
        allFixations(i).meanAmp_t1=tmp_mean_t1; allFixations(i).meanAmp_t2=tmp_mean_t2;
        allFixations(i).meanAmp_a1=tmp_mean_a1; allFixations(i).meanAmp_a2=tmp_mean_a2;
        allFixations(i).meanAmp_b1=tmp_mean_b1; allFixations(i).meanAmp_b2=tmp_mean_b2;
        allFixations(i).meanAmp_g1=tmp_mean_g1; allFixations(i).meanAmp_g2=tmp_mean_g2;
        
    end
    
    %% get left-right differences in the frequency bands power
    elecPairs = getElectrodePairs();
    
    %loop trhough all sentences
    for i=1:length(allFixations)
        tmp_mean_t1_diff=[];tmp_mean_t2_diff=[];
        tmp_mean_a1_diff=[];tmp_mean_a2_diff=[];
        tmp_mean_b1_diff=[];tmp_mean_b2_diff=[];
        tmp_mean_g1_diff=[];tmp_mean_g2_diff=[];
        
        %loop through all words within the current sentence:
        for ii=1:length(allFixations(i).word_EEGStart)
            
             % do not use data which was excluded in +-90 microvolt
            %thresholding (on sentence level)
            if not(allFixations(i).word_EEGStop(ii)==0)
               
                %loop through all electrodepairs for the current word
                for iii=1:length(elecPairs)
                    %find index of homologous electrodes of interest
                    i_l=find(strcmp({FullEEG.chanlocs.labels},elecPairs{iii,1}));
                    i_r=find(strcmp({FullEEG.chanlocs.labels},elecPairs{iii,2}));
                    
                    %theta:
                    tmp_mean_t1_diff(ii,iii)=allFixations(i).meanAmp_t1(ii,i_l)- allFixations(i).meanAmp_t1(ii,i_r);
                    tmp_mean_t2_diff(ii,iii)=allFixations(i).meanAmp_t2(ii,i_l)- allFixations(i).meanAmp_t2(ii,i_r);
                    %alpha:
                    tmp_mean_a1_diff(ii,iii)=allFixations(i).meanAmp_a1(ii,i_l)- allFixations(i).meanAmp_a1(ii,i_r);
                    tmp_mean_a2_diff(ii,iii)=allFixations(i).meanAmp_a2(ii,i_l)- allFixations(i).meanAmp_a2(ii,i_r);
                    %beta
                    tmp_mean_b1_diff(ii,iii)=allFixations(i).meanAmp_b1(ii,i_l)- allFixations(i).meanAmp_b1(ii,i_r);
                    tmp_mean_b2_diff(ii,iii)=allFixations(i).meanAmp_b2(ii,i_l)- allFixations(i).meanAmp_b2(ii,i_r);
                    %gamma
                    tmp_mean_g1_diff(ii,iii)=allFixations(i).meanAmp_g1(ii,i_l)- allFixations(i).meanAmp_g1(ii,i_r);
                    tmp_mean_g2_diff(ii,iii)=allFixations(i).meanAmp_g2(ii,i_l)- allFixations(i).meanAmp_g2(ii,i_r);
                end
            else
                
                tmp_mean_t1_diff(ii,:)=repmat(NaN,1, length(elecPairs));
                tmp_mean_t2_diff(ii,:)=repmat(NaN,1, length(elecPairs));
                %alpha:
                tmp_mean_a1_diff(ii,:)=repmat(NaN,1, length(elecPairs));
                tmp_mean_a2_diff(ii,:)=repmat(NaN,1, length(elecPairs));
                %beta
                tmp_mean_b1_diff(ii,:)=repmat(NaN,1, length(elecPairs));
                tmp_mean_b2_diff(ii,:)=repmat(NaN,1, length(elecPairs));
                %gamma
                tmp_mean_g1_diff(ii,:)=repmat(NaN,1, length(elecPairs));
                tmp_mean_g2_diff(ii,:)=repmat(NaN,1, length(elecPairs));
                
            end
        end
        allFixations(i).meanAmp_t1_diff=tmp_mean_t1_diff; allFixations(i).meanAmp_t2_diff=tmp_mean_t2_diff;
        allFixations(i).meanAmp_a1_diff=tmp_mean_a1_diff; allFixations(i).meanAmp_a2_diff=tmp_mean_a2_diff;
        allFixations(i).meanAmp_b1_diff=tmp_mean_b1_diff; allFixations(i).meanAmp_b2_diff=tmp_mean_b2_diff;
        allFixations(i).meanAmp_g1_diff=tmp_mean_g1_diff; allFixations(i).meanAmp_g2_diff=tmp_mean_g2_diff;
        
    end
    
    %% get theta alpha and beta power during each full sentence:
    
    sent_mean_t1=[];sent_mean_t2=[];
    sent_mean_a1=[];sent_mean_a2=[];
    sent_mean_b1=[];sent_mean_b2=[];
    sent_mean_g1=[];sent_mean_g2=[];
    
    for i=1:length(sentStart)
        
        currEEGStart=sentStart(i);
        currEEGStop=sentStop(i);
        
        % do not use data which was excluded in +-90 microvolt
        %thresholding (on sentence level)
        if not(currEEGStop==0)
            
            rawSentEEG{i}=FullEEG.data(1:nChans,currEEGStart: currEEGStop);
            
            %theta:
            sent_mean_t1(i,:)= mean(abs(hilbert(FullEEG.data_t1(1:nChans,currEEGStart:currEEGStop)')'),2)';
            sent_mean_t2(i,:)= mean(abs(hilbert(FullEEG.data_t2(1:nChans,currEEGStart:currEEGStop)')'),2)';
            %alpha:
            sent_mean_a1(i,:)= mean(abs(hilbert(FullEEG.data_a1(1:nChans,currEEGStart:currEEGStop)')'),2)';
            sent_mean_a2(i,:)= mean(abs(hilbert(FullEEG.data_a2(1:nChans,currEEGStart:currEEGStop)')'),2)';
            %beta
            sent_mean_b1(i,:)= mean(abs(hilbert(FullEEG.data_b1(1:nChans,currEEGStart:currEEGStop)')'),2)';
            sent_mean_b2(i,:)= mean(abs(hilbert(FullEEG.data_b2(1:nChans,currEEGStart:currEEGStop)')'),2)';
            %gamma
            sent_mean_g1(i,:)= mean(abs(hilbert(FullEEG.data_g1(1:nChans,currEEGStart:currEEGStop)')'),2)';
            sent_mean_g2(i,:)= mean(abs(hilbert(FullEEG.data_g2(1:nChans,currEEGStart:currEEGStop)')'),2)';
            
        else
            
            rawSentEEG{i}=NaN;
            
            sent_mean_t1(i,:)= repmat(NaN,1,105);
            sent_mean_t2(i,:)= repmat(NaN,1,105);
            %alpha:
            sent_mean_a1(i,:)= repmat(NaN,1,105);
            sent_mean_a2(i,:)= repmat(NaN,1,105);
            %beta
            sent_mean_b1(i,:)= repmat(NaN,1,105);
            sent_mean_b2(i,:)= repmat(NaN,1,105);
            %gamma
            sent_mean_g1(i,:)= repmat(NaN,1,105);
            sent_mean_g2(i,:)= repmat(NaN,1,105);
        end
        
    end
    
    
    %% calc diff scores for each electrode pair on sentence level
    for i=1:length(sentStart)
        
        % do not use data which was excluded in +-90 microvolt
        %thresholding (on sentence level)
        if not(sentStop(i)==0)
            
            for ii=1:length(elecPairs)
                
                %find index of homologous electrodes of interest
                i_l=find(strcmp({FullEEG.chanlocs.labels},elecPairs{ii,1}));
                i_r=find(strcmp({FullEEG.chanlocs.labels},elecPairs{ii,2}));
                
                %substract value of right electrode from left electrode in each
                %frequency band:
                
                %theta:
                sent_mean_t1_diff(i,ii)=sent_mean_t1(i,i_l)-sent_mean_t1(i,i_r);
                sent_mean_t2_diff(i,ii)=sent_mean_t2(i,i_l)-sent_mean_t2(i,i_r);
                %alpha:
                sent_mean_a1_diff(i,ii)=sent_mean_a1(i,i_l)-sent_mean_a1(i,i_r);
                sent_mean_a2_diff(i,ii)=sent_mean_a2(i,i_l)-sent_mean_a2(i,i_r);
                %beta
                sent_mean_b1_diff(i,ii)=sent_mean_b1(i,i_l)-sent_mean_b1(i,i_r);
                sent_mean_b2_diff(i,ii)=sent_mean_b2(i,i_l)-sent_mean_b2(i,i_r);
                %gamma
                sent_mean_g1_diff(i,ii)=sent_mean_g1(i,i_l)-sent_mean_g1(i,i_r);
                sent_mean_g2_diff(i,ii)=sent_mean_g2(i,i_l)-sent_mean_g2(i,i_r);
                
            end
        else
            sent_mean_t1_diff(i,:)=repmat(NaN,1,length(elecPairs));
            sent_mean_t2_diff(i,:)=repmat(NaN,1,length(elecPairs));
            %alpha:
            sent_mean_a1_diff(i,:)=repmat(NaN,1,length(elecPairs));
            sent_mean_a2_diff(i,:)=repmat(NaN,1,length(elecPairs));
            %beta
            sent_mean_b1_diff(i,:)=repmat(NaN,1,length(elecPairs));
            sent_mean_b2_diff(i,:)=repmat(NaN,1,length(elecPairs));
            %gamma
            sent_mean_g1_diff(i,:)=repmat(NaN,1,length(elecPairs));
            sent_mean_g2_diff(i,:)=repmat(NaN,1,length(elecPairs));
            
        end
    end
    
    
    
    %% write data of interest into useful struct ("sentenceData")
    %% and add ET features
    sentenceData=[];
    
    %loop thorugh all presented sentences:
    for i=1:length(allFixations)
        
        %get current sentence
        sent=sentences{i};
        sentenceData(i).content=sent;
        sent= strsplit(sent,' ');
        
        %features on sentence level:
        sentenceData(i).rawData=rawSentEEG{i};
        
        sentenceData(i).mean_t1=sent_mean_t1(i,:);
        sentenceData(i).mean_t2=sent_mean_t2(i,:);
        sentenceData(i).mean_a1=sent_mean_a1(i,:);
        sentenceData(i).mean_a2=sent_mean_a2(i,:);
        sentenceData(i).mean_b1=sent_mean_b1(i,:);
        sentenceData(i).mean_b2=sent_mean_b2(i,:);
        sentenceData(i).mean_g1=sent_mean_g1(i,:);
        sentenceData(i).mean_g2=sent_mean_g2(i,:);
        
        sentenceData(i).mean_t1_diff=sent_mean_t1_diff(i,:);
        sentenceData(i).mean_t2_diff=sent_mean_t2_diff(i,:);
        sentenceData(i).mean_a1_diff=sent_mean_a1_diff(i,:);
        sentenceData(i).mean_a2_diff=sent_mean_a2_diff(i,:);
        sentenceData(i).mean_b1_diff=sent_mean_b1_diff(i,:);
        sentenceData(i).mean_b2_diff=sent_mean_b2_diff(i,:);
        sentenceData(i).mean_g1_diff=sent_mean_g1_diff(i,:);
        sentenceData(i).mean_g2_diff=sent_mean_g2_diff(i,:);
        
        
        
        % get data for each word of the sentence:
        for ii=1:size(bounds{i},1)
            
            %save wordname:
            sentenceData(i).word(ii).content= sent{ii};
            
            %get all fixations on the current word:
            fixPos= find(allFixations(i).words==ii);
            
            %get the corresponding data:
            if not(isempty(fixPos)) %if there is any fixation on the word
                sentenceData(i).word(ii).fixPositions=fixPos;
                sentenceData(i).word(ii).nFixations=length(fixPos);
                sentenceData(i).word(ii).meanPupilSize= mean(allFixations(i).word_avgPupilsize(fixPos));
                
                
                % xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
                % include raw eeg data                
                rawEEGstart= allFixations(i).word_EEGStart(fixPos);
                rawEEGstop=allFixations(i).word_EEGStop(fixPos);
                
                for k=1:length(rawEEGstart)
                    % do not use data if marked as bad:
                    if not(rawEEGstop(k)==0)
                        sentenceData(i).word(ii).rawEEG{k}=FullEEG.data(1:nChans,rawEEGstart(k):rawEEGstop(k));
                        sentenceData(i).word(ii).rawET{k}=FullEEG.data(nChans+1:end,rawEEGstart(k):rawEEGstop(k));
                    else
                        sentenceData(i).word(ii).rawEEG{k}=NaN;
                        sentenceData(i).word(ii).rawET{k}=FullEEG.data(nChans+1:end,rawEEGstart(k):rawEEGstop(k));
                        
                    end
                    
                end
                %xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
                
                
                % extract and save eyetracking features:
                
                % ####### only examine First Fixation on word (FFD) ###########
                sentenceData(i).word(ii).FFD=allFixations(i).word_fixationDuration(fixPos(1));
                sentenceData(i).word(ii).FFD_pupilsize= allFixations(i).word_avgPupilsize(fixPos(1));
                %frequency power during first fixation on current word:
                sentenceData(i).word(ii).FFD_t1=allFixations(i).meanAmp_t1(fixPos(1),1:nChans);
                sentenceData(i).word(ii).FFD_t2=allFixations(i).meanAmp_t2(fixPos(1),1:nChans);
                sentenceData(i).word(ii).FFD_a1=allFixations(i).meanAmp_a1(fixPos(1),1:nChans);
                sentenceData(i).word(ii).FFD_a2=allFixations(i).meanAmp_a2(fixPos(1),1:nChans);
                sentenceData(i).word(ii).FFD_b1=allFixations(i).meanAmp_b1(fixPos(1),1:nChans);
                sentenceData(i).word(ii).FFD_b2=allFixations(i).meanAmp_b2(fixPos(1),1:nChans);
                sentenceData(i).word(ii).FFD_g1=allFixations(i).meanAmp_g1(fixPos(1),1:nChans);
                sentenceData(i).word(ii).FFD_g2=allFixations(i).meanAmp_g2(fixPos(1),1:nChans);
                %frequency power difference during first fixation on current word:
                sentenceData(i).word(ii).FFD_t1_diff=allFixations(i).meanAmp_t1_diff(fixPos(1),:);
                sentenceData(i).word(ii).FFD_t2_diff=allFixations(i).meanAmp_t2_diff(fixPos(1),:);
                sentenceData(i).word(ii).FFD_a1_diff=allFixations(i).meanAmp_a1_diff(fixPos(1),:);
                sentenceData(i).word(ii).FFD_a2_diff=allFixations(i).meanAmp_a2_diff(fixPos(1),:);
                sentenceData(i).word(ii).FFD_b1_diff=allFixations(i).meanAmp_b1_diff(fixPos(1),:);
                sentenceData(i).word(ii).FFD_b2_diff=allFixations(i).meanAmp_b2_diff(fixPos(1),:);
                sentenceData(i).word(ii).FFD_g1_diff=allFixations(i).meanAmp_g1_diff(fixPos(1),:);
                sentenceData(i).word(ii).FFD_g2_diff=allFixations(i).meanAmp_g2_diff(fixPos(1),:);
                % #############################################################
                
                
                % ######### only examine first and single fixation (SFD, if existing) #######
                if length(fixPos)==1
                    sentenceData(i).word(ii).SFD=allFixations(i).word_fixationDuration(fixPos(1));
                    sentenceData(i).word(ii).SFD_pupilsize= allFixations(i).word_avgPupilsize(fixPos(1));
                    %frequency power during first and only fixation on current word:
                    sentenceData(i).word(ii).SFD_t1=allFixations(i).meanAmp_t1(fixPos(1),1:nChans);
                    sentenceData(i).word(ii).SFD_t2=allFixations(i).meanAmp_t2(fixPos(1),1:nChans);
                    sentenceData(i).word(ii).SFD_a1=allFixations(i).meanAmp_a1(fixPos(1),1:nChans);
                    sentenceData(i).word(ii).SFD_a2=allFixations(i).meanAmp_a2(fixPos(1),1:nChans);
                    sentenceData(i).word(ii).SFD_b1=allFixations(i).meanAmp_b1(fixPos(1),1:nChans);
                    sentenceData(i).word(ii).SFD_b2=allFixations(i).meanAmp_b2(fixPos(1),1:nChans);
                    sentenceData(i).word(ii).SFD_g1=allFixations(i).meanAmp_g1(fixPos(1),1:nChans);
                    sentenceData(i).word(ii).SFD_g2=allFixations(i).meanAmp_g2(fixPos(1),1:nChans);
                    
                    %frequency power diffenece during first and only fixation on current word:
                    sentenceData(i).word(ii).SFD_t1_diff=allFixations(i).meanAmp_t1_diff(fixPos(1),:);
                    sentenceData(i).word(ii).SFD_t2_diff=allFixations(i).meanAmp_t2_diff(fixPos(1),:);
                    sentenceData(i).word(ii).SFD_a1_diff=allFixations(i).meanAmp_a1_diff(fixPos(1),:);
                    sentenceData(i).word(ii).SFD_a2_diff=allFixations(i).meanAmp_a2_diff(fixPos(1),:);
                    sentenceData(i).word(ii).SFD_b1_diff=allFixations(i).meanAmp_b1_diff(fixPos(1),:);
                    sentenceData(i).word(ii).SFD_b2_diff=allFixations(i).meanAmp_b2_diff(fixPos(1),:);
                    sentenceData(i).word(ii).SFD_g1_diff=allFixations(i).meanAmp_g1_diff(fixPos(1),:);
                    sentenceData(i).word(ii).SFD_g2_diff=allFixations(i).meanAmp_g2_diff(fixPos(1),:);
                end
                % ###########################################################
                
                % ########## examine total number of fixations (TRT) ##########
                sentenceData(i).word(ii).TRT=sum(allFixations(i).word_fixationDuration(fixPos));
                sentenceData(i).word(ii).TRT_pupilsize= mean(allFixations(i).word_avgPupilsize(fixPos));
                % mean frequency power during all fixation on current word:
                sentenceData(i).word(ii).TRT_t1=nanmean(allFixations(i).meanAmp_t1(fixPos,1:nChans),1);%changeMe
                sentenceData(i).word(ii).TRT_t2=nanmean(allFixations(i).meanAmp_t2(fixPos,1:nChans),1);
                sentenceData(i).word(ii).TRT_a1=nanmean(allFixations(i).meanAmp_a1(fixPos,1:nChans),1);
                sentenceData(i).word(ii).TRT_a2=nanmean(allFixations(i).meanAmp_a2(fixPos,1:nChans),1);
                sentenceData(i).word(ii).TRT_b1=nanmean(allFixations(i).meanAmp_b1(fixPos,1:nChans),1);
                sentenceData(i).word(ii).TRT_b2=nanmean(allFixations(i).meanAmp_b2(fixPos,1:nChans),1);
                sentenceData(i).word(ii).TRT_g1=nanmean(allFixations(i).meanAmp_g1(fixPos,1:nChans),1);
                sentenceData(i).word(ii).TRT_g2=nanmean(allFixations(i).meanAmp_g2(fixPos,1:nChans),1);
                % mean frequency power difference during all fixation on current word:
                sentenceData(i).word(ii).TRT_t1_diff=nanmean(allFixations(i).meanAmp_t1_diff(fixPos,:),1);
                sentenceData(i).word(ii).TRT_t2_diff=nanmean(allFixations(i).meanAmp_t2_diff(fixPos,:),1);
                sentenceData(i).word(ii).TRT_a1_diff=nanmean(allFixations(i).meanAmp_a1_diff(fixPos,:),1);
                sentenceData(i).word(ii).TRT_a2_diff=nanmean(allFixations(i).meanAmp_a2_diff(fixPos,:),1);
                sentenceData(i).word(ii).TRT_b1_diff=nanmean(allFixations(i).meanAmp_b1_diff(fixPos,:),1);
                sentenceData(i).word(ii).TRT_b2_diff=nanmean(allFixations(i).meanAmp_b2_diff(fixPos,:),1);
                sentenceData(i).word(ii).TRT_g1_diff=nanmean(allFixations(i).meanAmp_g1_diff(fixPos,:),1);
                sentenceData(i).word(ii).TRT_g2_diff=nanmean(allFixations(i).meanAmp_g2_diff(fixPos,:),1);
                % #############################################################
                
                % ############### examine gaze duration GD ####################
                % that is: only fixations before eyes left word for the first time
                if length(fixPos)>1
                    
                    %find relevant fixations:
                    fixPosGD=[];
                    for j=1:length(fixPos)-1
                        if fixPos(j+1)==fixPos(j)+1;
                            fixPosGD(j)=fixPos(j);
                            fixPosGD(j+1)=fixPos(j+1);
                        else
                            fixPosGD(j)=fixPos(j);
                            break;
                        end
                    end
                    
                    % extract corresponding GD data:
                    sentenceData(i).word(ii).GD=sum(allFixations(i).word_fixationDuration(fixPosGD));
                    sentenceData(i).word(ii).GD_pupilsize= mean(allFixations(i).word_avgPupilsize(fixPosGD));
                    % mean frequency power during all fixation on current word:
                    sentenceData(i).word(ii).GD_t1=nanmean(allFixations(i).meanAmp_t1(fixPosGD,1:nChans),1);%changeMe
                    sentenceData(i).word(ii).GD_t2=nanmean(allFixations(i).meanAmp_t2(fixPosGD,1:nChans),1);
                    sentenceData(i).word(ii).GD_a1=nanmean(allFixations(i).meanAmp_a1(fixPosGD,1:nChans),1);
                    sentenceData(i).word(ii).GD_a2=nanmean(allFixations(i).meanAmp_a2(fixPosGD,1:nChans),1);
                    sentenceData(i).word(ii).GD_b1=nanmean(allFixations(i).meanAmp_b1(fixPosGD,1:nChans),1);
                    sentenceData(i).word(ii).GD_b2=nanmean(allFixations(i).meanAmp_b2(fixPosGD,1:nChans),1);
                    sentenceData(i).word(ii).GD_g1=nanmean(allFixations(i).meanAmp_g1(fixPosGD,1:nChans),1);
                    sentenceData(i).word(ii).GD_g2=nanmean(allFixations(i).meanAmp_g2(fixPosGD,1:nChans),1);
                    % mean frequency power during all fixation on current word:
                    sentenceData(i).word(ii).GD_t1_diff=nanmean(allFixations(i).meanAmp_t1_diff(fixPosGD,:),1);
                    sentenceData(i).word(ii).GD_t2_diff=nanmean(allFixations(i).meanAmp_t2_diff(fixPosGD,:),1);
                    sentenceData(i).word(ii).GD_a1_diff=nanmean(allFixations(i).meanAmp_a1_diff(fixPosGD,:),1);
                    sentenceData(i).word(ii).GD_a2_diff=nanmean(allFixations(i).meanAmp_a2_diff(fixPosGD,:),1);
                    sentenceData(i).word(ii).GD_b1_diff=nanmean(allFixations(i).meanAmp_b1_diff(fixPosGD,:),1);
                    sentenceData(i).word(ii).GD_b2_diff=nanmean(allFixations(i).meanAmp_b2_diff(fixPosGD,:),1);
                    sentenceData(i).word(ii).GD_g1_diff=nanmean(allFixations(i).meanAmp_g1_diff(fixPosGD,:),1);
                    sentenceData(i).word(ii).GD_g2_diff=nanmean(allFixations(i).meanAmp_g2_diff(fixPosGD,:),1);
                    %if there is only one fixation, GD measures are the same as SFD
                else
                    sentenceData(i).word(ii).GD= sentenceData(i).word(ii).SFD;
                    sentenceData(i).word(ii).GD_pupilsize=sentenceData(i).word(ii).SFD_pupilsize;
                    
                    sentenceData(i).word(ii).GD_t1=sentenceData(i).word(ii).SFD_t1;
                    sentenceData(i).word(ii).GD_t2=sentenceData(i).word(ii).SFD_t2;
                    sentenceData(i).word(ii).GD_a1=sentenceData(i).word(ii).SFD_a1;
                    sentenceData(i).word(ii).GD_a2=sentenceData(i).word(ii).SFD_a2;
                    sentenceData(i).word(ii).GD_b1=sentenceData(i).word(ii).SFD_b1;
                    sentenceData(i).word(ii).GD_b2=sentenceData(i).word(ii).SFD_b2;
                    sentenceData(i).word(ii).GD_g1=sentenceData(i).word(ii).SFD_g1;
                    sentenceData(i).word(ii).GD_g2=sentenceData(i).word(ii).SFD_g2;
                    %same for difference spectrum
                    sentenceData(i).word(ii).GD_t1_diff=sentenceData(i).word(ii).SFD_t1_diff;
                    sentenceData(i).word(ii).GD_t2_diff=sentenceData(i).word(ii).SFD_t2_diff;
                    sentenceData(i).word(ii).GD_a1_diff=sentenceData(i).word(ii).SFD_a1_diff;
                    sentenceData(i).word(ii).GD_a2_diff=sentenceData(i).word(ii).SFD_a2_diff;
                    sentenceData(i).word(ii).GD_b1_diff=sentenceData(i).word(ii).SFD_b1_diff;
                    sentenceData(i).word(ii).GD_b2_diff=sentenceData(i).word(ii).SFD_b2_diff;
                    sentenceData(i).word(ii).GD_g1_diff=sentenceData(i).word(ii).SFD_g1_diff;
                    sentenceData(i).word(ii).GD_g2_diff=sentenceData(i).word(ii).SFD_g2_diff;
                end
                % #############################################################
                
                % ###### examine go-past time GPT #################################
                % that is: sum of all fixations prior to processing of word to
                % the right (including regressions)
                fixPosGPT=[];
                %if the first fixation on the current fixated word is the last
                % word in the list of fixations of the sentence (means: single
                % fixation),
                if fixPos(1)==length(allFixations(i).words)
                    fixPosGPT=[fixPosGPT fixPos(1)];
                    %if the next word is the same or to the left of the current word:
                elseif allFixations(i).words(fixPos(1))>= allFixations(i).words(fixPos(1)+1)
                    
                    
                    currWord= allFixations(i).words(fixPos(1));
                    nextWord=allFixations(i).words(fixPos(1)+1);
                    currInd=fixPos(1);
                    nextInd=fixPos(1)+1;
                    nFixations=length(allFixations(i).words);
                    % while we dont run out of index of wordifxations and
                    % next fixated word is the same or left word
                    while nextInd<=nFixations &&  currWord <= allFixations(i).words(fixPos(1))
                        
                        fixPosGPT=[fixPosGPT currInd];
    
                        if nextInd==nFixations && nextWord <= allFixations(i).words(fixPos(1))
                            fixPosGPT=[fixPosGPT nextInd];
                            nextInd=nextInd+1;
                        elseif nextInd==nFixations
                            nextInd=nextInd+1;
                        else
                            %move on:
                            currInd=nextInd;
                            nextInd=nextInd+1;
                            currWord= allFixations(i).words(currInd);
                            nextWord=allFixations(i).words(nextInd);
                        end
                    end
                    %if next word i to the right - its only a single fixation
                elseif allFixations(i).words(fixPos(1))< allFixations(i).words(fixPos(1)+1)
                    fixPosGPT=[fixPosGPT fixPos(1)];
                end
                
                % extract corresponding GPT data:
                sentenceData(i).word(ii).GPT=sum(allFixations(i).word_fixationDuration(fixPosGPT));
                sentenceData(i).word(ii).GPT_pupilsize= mean(allFixations(i).word_avgPupilsize(fixPosGPT));
                
                % mean frequency power during all fixation on current word:
                sentenceData(i).word(ii).GPT_t1=nanmean(allFixations(i).meanAmp_t1(fixPosGPT,1:nChans),1);%changeMe
                sentenceData(i).word(ii).GPT_t2=nanmean(allFixations(i).meanAmp_t2(fixPosGPT,1:nChans),1);
                sentenceData(i).word(ii).GPT_a1=nanmean(allFixations(i).meanAmp_a1(fixPosGPT,1:nChans),1);
                sentenceData(i).word(ii).GPT_a2=nanmean(allFixations(i).meanAmp_a2(fixPosGPT,1:nChans),1);
                sentenceData(i).word(ii).GPT_b1=nanmean(allFixations(i).meanAmp_b1(fixPosGPT,1:nChans),1);
                sentenceData(i).word(ii).GPT_b2=nanmean(allFixations(i).meanAmp_b2(fixPosGPT,1:nChans),1);
                sentenceData(i).word(ii).GPT_g1=nanmean(allFixations(i).meanAmp_g1(fixPosGPT,1:nChans),1);
                sentenceData(i).word(ii).GPT_g2=nanmean(allFixations(i).meanAmp_g2(fixPosGPT,1:nChans),1);
                % mean frequency power differnce during all fixation on current word:
                sentenceData(i).word(ii).GPT_t1_diff=nanmean(allFixations(i).meanAmp_t1_diff(fixPosGPT,:),1);
                sentenceData(i).word(ii).GPT_t2_diff=nanmean(allFixations(i).meanAmp_t2_diff(fixPosGPT,:),1);
                sentenceData(i).word(ii).GPT_a1_diff=nanmean(allFixations(i).meanAmp_a1_diff(fixPosGPT,:),1);
                sentenceData(i).word(ii).GPT_a2_diff=nanmean(allFixations(i).meanAmp_a2_diff(fixPosGPT,:),1);
                sentenceData(i).word(ii).GPT_b1_diff=nanmean(allFixations(i).meanAmp_b1_diff(fixPosGPT,:),1);
                sentenceData(i).word(ii).GPT_b2_diff=nanmean(allFixations(i).meanAmp_b2_diff(fixPosGPT,:),1);
                sentenceData(i).word(ii).GPT_g1_diff=nanmean(allFixations(i).meanAmp_g1_diff(fixPosGPT,:),1);
                sentenceData(i).word(ii).GPT_g2_diff=nanmean(allFixations(i).meanAmp_g2_diff(fixPosGPT,:),1);
                
                
                
                %##############################################################
            else
                %if there is not a single fixation on the current word:
                %fill struct with empty values:
                
                sentenceData(i).word(ii).fixPositions=[];
                sentenceData(i).word(ii).nFixations=[];
                sentenceData(i).word(ii).meanPupilSize=[];
                
                % ####### only examine First Fixation on word (FFD) ###########
                sentenceData(i).word(ii).FFD=[];
                sentenceData(i).word(ii).FFD_pupilsize=[];
                sentenceData(i).word(ii).FFD_t1=[];
                sentenceData(i).word(ii).FFD_t2=[];
                sentenceData(i).word(ii).FFD_a1=[];
                sentenceData(i).word(ii).FFD_a2=[];
                sentenceData(i).word(ii).FFD_b1=[];
                sentenceData(i).word(ii).FFD_b2=[];
                sentenceData(i).word(ii).FFD_g1=[];
                sentenceData(i).word(ii).FFD_g2=[];
                sentenceData(i).word(ii).FFD_t1_diff=[];
                sentenceData(i).word(ii).FFD_t2_diff=[];
                sentenceData(i).word(ii).FFD_a1_diff=[];
                sentenceData(i).word(ii).FFD_a2_diff=[];
                sentenceData(i).word(ii).FFD_b1_diff=[];
                sentenceData(i).word(ii).FFD_b2_diff=[];
                sentenceData(i).word(ii).FFD_g1_diff=[];
                sentenceData(i).word(ii).FFD_g2_diff=[];
                sentenceData(i).word(ii).TRT=[];
                sentenceData(i).word(ii).TRT_pupilsize=[];
                sentenceData(i).word(ii).TRT_t1=[];
                sentenceData(i).word(ii).TRT_t2=[];
                sentenceData(i).word(ii).TRT_a1=[];
                sentenceData(i).word(ii).TRT_a2=[];
                sentenceData(i).word(ii).TRT_b1=[];
                sentenceData(i).word(ii).TRT_b2=[];
                sentenceData(i).word(ii).TRT_g1=[];
                sentenceData(i).word(ii).TRT_g2=[];
                sentenceData(i).word(ii).TRT_t1_diff=[];
                sentenceData(i).word(ii).TRT_t2_diff=[];
                sentenceData(i).word(ii).TRT_a1_diff=[];
                sentenceData(i).word(ii).TRT_a2_diff=[];
                sentenceData(i).word(ii).TRT_b1_diff=[];
                sentenceData(i).word(ii).TRT_b2_diff=[];
                sentenceData(i).word(ii).TRT_g1_diff=[];
                sentenceData(i).word(ii).TRT_g2_diff=[];
                sentenceData(i).word(ii).GD=[];
                sentenceData(i).word(ii).GD_pupilsize=[];
                sentenceData(i).word(ii).GD_t1=[];
                sentenceData(i).word(ii).GD_t2=[];
                sentenceData(i).word(ii).GD_a1=[];
                sentenceData(i).word(ii).GD_a2=[];
                sentenceData(i).word(ii).GD_b1=[];
                sentenceData(i).word(ii).GD_b2=[];
                sentenceData(i).word(ii).GD_g1=[];
                sentenceData(i).word(ii).GD_g2=[];
                sentenceData(i).word(ii).GD_t1_diff=[];
                sentenceData(i).word(ii).GD_t2_diff=[];
                sentenceData(i).word(ii).GD_a1_diff=[];
                sentenceData(i).word(ii).GD_a2_diff=[];
                sentenceData(i).word(ii).GD_b1_diff=[];
                sentenceData(i).word(ii).GD_b2_diff=[];
                sentenceData(i).word(ii).GD_g1_diff=[];
                sentenceData(i).word(ii).GD_g2_diff=[];
                sentenceData(i).word(ii).GPT=[];
                sentenceData(i).word(ii).GPT_pupilsize=[];
                sentenceData(i).word(ii).GPT_t1=[];
                sentenceData(i).word(ii).GPT_t2=[];
                sentenceData(i).word(ii).GPT_a1=[];
                sentenceData(i).word(ii).GPT_a2=[];
                sentenceData(i).word(ii).GPT_b1=[];
                sentenceData(i).word(ii).GPT_b2=[];
                sentenceData(i).word(ii).GPT_g1=[];
                sentenceData(i).word(ii).GPT_g2=[];
                sentenceData(i).word(ii).GPT_t1_diff=[];
                sentenceData(i).word(ii).GPT_t2_diff=[];
                sentenceData(i).word(ii).GPT_a1_diff=[];
                sentenceData(i).word(ii).GPT_a2_diff=[];
                sentenceData(i).word(ii).GPT_b1_diff=[];
                sentenceData(i).word(ii).GPT_b2_diff=[];
                sentenceData(i).word(ii).GPT_g1_diff=[];
                sentenceData(i).word(ii).GPT_g2_diff=[];
            end
        end
        
        %calculate omission rate for each sentence:
        skipped=0;
        for ii=1:size(bounds{i},1)
            if isempty(sentenceData(i).word(ii).fixPositions)
                skipped=skipped+1;
            end
        end
        sentenceData(i).omissionRate=skipped/size(bounds{i},1);
        
        %save full fixation data of sentence
        sentenceData(i).allFixations.x=allFixations(i).x;
        sentenceData(i).allFixations.y=allFixations(i).y;
        sentenceData(i).allFixations.duration=allFixations(i).duration;
        sentenceData(i).allFixations.pupilsize=allFixations(i).pupilsize;
        
        %save matching wordbounds of the current sentence:
        sentenceData(i).wordbounds=bounds{i};
        
    end
    
  
    disp('done - now saving the file...');
    save([prepocFold filesep 'firstLevelResults' filesep 'results' subject '_NR.mat'], 'sentenceData');
end
