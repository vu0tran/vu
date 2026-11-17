import * as LM from 'pk';
import { ContentBlock } from 'pk';
function isR(b: LM.ContentBlock): b is LM.ContentBlock.Reasoning { return b.type === 'reasoning'; }
const x: LM.ContentBlock.Reasoning = { type: 'reasoning', r: 1 };
const y: ContentBlock.Reasoning = { type: 'reasoning', r: 1 };
const z: LM.ContentBlock.Multimodal.Standard = { type: 'x' };
