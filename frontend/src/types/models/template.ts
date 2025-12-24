/**
 * Template model types
 */
import { StoryPattern } from "../enums";

export interface TemplateField {
  name: string;
  type: "text" | "number" | "date" | "select";
  required: boolean;
  defaultValue?: any;
  options?: string[]; // select型の場合
}

export interface StoryTemplate {
  id: string;
  name: string;
  pattern: StoryPattern;
  fields: TemplateField[];
  checklist: string[];
  defaultEstimate: number;
  isCustom: boolean;
  userId?: string; // カスタムテンプレートの場合
}
