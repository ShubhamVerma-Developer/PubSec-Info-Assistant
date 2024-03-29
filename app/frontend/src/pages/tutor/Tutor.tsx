// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

import React from 'react';
//import { Button } from '@fluentui/react';
import { Accordion, Card, Button } from 'react-bootstrap';
import {getHint, processAgentResponse, getSolve, streamData} from "../../api";
import { useEffect, useState } from "react";
import styles from './Tutor.module.css';
import ReactMarkdown from 'react-markdown';

const Tutor = () => {
    const [loading, setLoading] = useState(false);
    const [mathProblem, setMathProblem] = useState('');
    const [output, setOutput] = useState(['']);
    //const [output, setOutput] = useState<string | null>("");
    const [selectedButton, setSelectedButton] = useState<string | null>(null);


    const handleInput = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setLoading(true);
        userInput(mathProblem);
    };

    const userInput = (problem: string) => {
        // Process the user's math problem here
        console.log(problem);
        setLoading(false);
    };
    async function hinter(question: string) {
        try {
            setOutput(['']);
            setLoading(true);
            const hint: String = await getHint(question);
            setLoading(false);
            setOutput([hint.toString()]);
            console.log(hint);
        } catch (error) {
            console.log(error);
        }
    }
    
    async function getAnswer(question: string) {
        setOutput(['']);
        setLoading(true);
        const result = await processAgentResponse(question);
        setLoading(false);
        setOutput([result.toString()]);
        // const eventSource = await processAgentResponse(question);
        // eventSource.onmessage = function(event) {
        //     console.log(event.data);
        //     setOutput(event.data);
    };
    const [eventSource, setEventSource] = useState<EventSource | null>(null);

    const handleButton2Click = () => {
        setOutput(['']);
        setLoading(true);
        setSelectedButton('button2');
        if (eventSource) {
          eventSource.close();
        }
        const newEventSource = streamData(mathProblem, (data) => {
          setOutput((prevOutput) => [...prevOutput, data]);
        });
        setEventSource(newEventSource);
      };
  
    useEffect(() => {
      return () => {
        if (eventSource) {
          eventSource.close();
        }
      };
    }, [eventSource]);
return (
    <div>
    <h1 className={styles.title}>Your Friendly Math Tutor</h1>
    <div className={styles.centeredContainer}>
        <form className={styles.formClass} onSubmit={handleInput}>
            <p className={styles.inputLabel}>Enter question:</p>
            <input
                className={styles.inputField}
                type="text"
                value={mathProblem}
                onChange={(e) => setMathProblem(e.target.value)}
                placeholder="Enter question:"
            />
            <div className={styles.buttonContainer}>
            <Button variant="secondary"
                className={selectedButton === 'button1' ? styles.selectedButton : ''}
                onClick={() => {
                    setSelectedButton('button1');
                    hinter(mathProblem);
                }}
            >
                Give me clues
            </Button>
            <Button variant="secondary"
                className={selectedButton === 'button2' ? styles.selectedButton : ''}
                onClick={() => {
                    setSelectedButton('button2');
                    // solver(mathProblem);
                    handleButton2Click();
                }}
            >
                Show me how to solve it
            </Button>
            <Button variant="secondary"
                className={selectedButton === 'button3' ? styles.selectedButton : ''}
                onClick={() => {
                    setSelectedButton("button3");
                    getAnswer(mathProblem);
                }}
            >
                Show me the answer
            </Button>
        </div>
        </form>
        {loading && <div className="spinner">Loading...</div>}
        {output && output.join('') !== '' &&
                <Accordion defaultActiveKey="0">                   
                    <h2>
                        Math Tutor Response:
                    </h2>
                    <Accordion.Collapse eventKey="0">
                        <div>
                        {output.map((item, index) => (
                        <ReactMarkdown key={index} children={item} />
                        ))}
                    </div>
                    </Accordion.Collapse>                    
                </Accordion>
            }
    </div>
    </div>
)
};

export default Tutor; // Export the 'Chat' component
