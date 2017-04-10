# Text Summarizer
This is a simple text summarizer using a sentencer, depenency parser and reconstructor.  

## Stack Used
- Python 3.5  
- NLTK  
- Stanford Dependency Parser (Used as a backgroud daemon)
	- http://nlp.stanford.edu/software/stanford-english-corenlp-2016-10-31-models.jar
	- http://nlp.stanford.edu/software/stanford-english-kbp-corenlp-2016-10-31-models.jar
	- http://nlp.stanford.edu/software/stanford-corenlp-models-current.jar

## Commands to run this
- ```java -cp "*" -Xmx2g edu.stanford.nlp.pipeline.StanfordCoreNLP -annotators tokenize,ssplit,pos,lemma,ner,parse,dcoref,depparse -file input/input.txt```

## Output
- This generates an output file named ```input.txt.out``` which contains:  
	- tokenised pos tags on tokens
	- A sentencer breaks down paras to sentences and then further breaks each sentence to generate
	dependencies.

## Todo
- Make a daemon process
- Implement a triple store
- Reconstruct sentences